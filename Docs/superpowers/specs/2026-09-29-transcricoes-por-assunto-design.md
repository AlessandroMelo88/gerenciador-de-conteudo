# Transcrições completas organizadas por assunto

**Status:** aguardando revisão da especificação  
**Data:** 29/09/2026  
**Escopo:** Hacker Libertário, com Fabio Akita como fonte prioritária

## Contexto

O pipeline já arquiva `transcript_text` e `transcript_data` em `source_videos`. O JSON mantém
o texto completo e os segmentos com timestamps, necessários para selecionar momentos e gerar
legendas. Hoje esses dados não têm uma organização persistida por assunto que permita consultar
e reutilizar cada parte da aula/vídeo.

Para o cron nativo local do Hacker Libertário, a conexão verificada em 29/09/2026 é PostgreSQL 18.3
(Homebrew), base `clips_automation`; `pgvector` ainda não está disponível. Produção usa PostgreSQL
17 e o Compose local é um terceiro ambiente, separado. A organização temática deve permanecer no
banco nativo existente, junto do vídeo de origem; não criar outro banco vetorial nesta etapa. Ver
[ADR-0007](../../../Docs/ADR/0007-postgresql-18-nativo-pgvector.md) para a decisão de versão e
ativação pendente do pgvector.

Fabio Akita já está cadastrado como fonte do nicho `hacker-libertario`, com prioridade de entrada
ajustada para `+10` na escala existente de `-10` a `+10`. Essa prioridade afeta a ordem de entrada
na fila; ela não substitui a prioridade editorial dos vídeos nem altera o arquivo/transcrição.

## Objetivo

Guardar no banco a transcrição integral e original de cada vídeo e disponibilizá-la dividida em
grupos de assuntos cronológicos, preservando para cada grupo os timestamps e o trecho literal que
veio da transcrição. A divisão deve ajudar a pesquisar e reaproveitar o conhecimento sem perder a
ligação com o vídeo original.

## Decisões aprovadas

1. Manter `source_videos.transcript_text` e `source_videos.transcript_data` como cópia canônica da
   transcrição integral e dos segmentos temporizados.
2. Usar o PostgreSQL existente; não abrir banco separado para transcrições ou tópicos.
3. Persistir os grupos em uma tabela filha `source_video_topics`, ligada a `source_videos`.
4. Cada grupo representa uma faixa cronológica contígua de segmentos da transcrição.
5. Usar IA para identificar e nomear assuntos, mas não para reescrever a transcrição. O texto de
   cada grupo será montado a partir dos segmentos originais correspondentes.
6. Uma falha ao separar assuntos não pode apagar, substituir ou invalidar a transcrição integral.
   A separação deve poder ser tentada novamente.
7. Priorizar Fabio Akita já cadastrado em `hacker-libertario`; a prioridade padrão de outras fontes
   continua editável ao longo do tempo, conforme o interesse editorial.

## Modelo de dados

Adicionar `source_video_topics` com:

| Campo | Uso |
|---|---|
| `id` | Chave primária |
| `source_video_id` | FK para `source_videos.id` |
| `position` | Ordem cronológica do grupo no vídeo |
| `title` | Nome curto do assunto |
| `start_seconds` / `end_seconds` | Limites temporais derivados dos segmentos |
| `first_segment_index` / `last_segment_index` | Índices inclusivos na lista canônica de segmentos |
| `transcript_text` | Concatenação literal dos textos dos segmentos cobertos |
| `created_at` / `updated_at` | Auditoria e atualização |

Restrições: unicidade de `(source_video_id, position)`, `end_seconds >= start_seconds`, índices por
vídeo e ordem, e FK sem cascade, seguindo a regra atual do domínio. O caminho de remoção deverá
tratar explicitamente grupos antes de remover um vídeo.

Não armazenar resumo gerado nesta primeira versão: o requisito é manter o conteúdo literal completo
e separado por assunto. Resumo, embeddings e busca semântica ficam fora deste escopo.

## Fluxo de processamento

1. Obter a transcrição, preferindo legendas disponíveis da fonte quando forem utilizáveis e
   recorrendo ao transcritor atual quando necessário.
2. Validar que `text` não está vazio e que há segmentos temporizados utilizáveis. Preservar o
   resultado integral em `source_videos.transcript_text` e `transcript_data` antes de iniciar a
   divisão temática.
3. Enviar todos os segmentos à etapa de classificação temática. Se o limite de contexto exigir
   blocos, os blocos devem cobrir toda a lista, usar índices globais e ter sobreposição suficiente
   para reconciliar assuntos que atravessam fronteiras.
4. Solicitar títulos de assunto e faixas de segmentos. A resposta da IA identifica segmentos; não
   fornece texto de transcrição substituto.
5. Validar que os grupos estão em ordem, não se sobrepõem e cobrem todos os segmentos de texto
   exatamente uma vez. Mesclar grupos adjacentes que tenham o mesmo assunto quando apropriado.
6. Reconstruir `transcript_text` de cada linha a partir da transcrição canônica. Gravar o conjunto
   novo em transação, sem deixar metade dos grupos antigos misturados com metade dos novos.
7. Se a etapa falhar, manter a transcrição integral intacta, registrar estado/erro recuperável para
   nova tentativa e não avançar como se a divisão temática estivesse completa.

Reprocessar deve substituir de forma atômica os grupos daquele vídeo e ser idempotente para a mesma
versão da transcrição. Alterar a transcrição invalida os grupos anteriores até que uma nova
separação válida seja persistida.

## Ingestão e recuperação de dados existentes

- Executar a separação para os sete vídeos de Fabio Akita que já têm transcrição integral disponível
  no banco/sidecar, validando correspondência com seus segmentos originais.
- Para os dez vídeos sem transcrição persistida, procurar legendas/captions disponíveis antes de
  baixar novamente o vídeo bruto. Só considerar a transcrição concluída depois de salvá-la por
  inteiro no banco; a criação de grupos vem depois.
- Não fazer a integridade do arquivo bruto ser pré-requisito para consultar transcrições e tópicos
  que já estejam salvos.
- Não iniciar consumidores no estado atual do Compose sem antes corrigir a referência inválida ao
  volume `videos`; o trabalho de implementação deve conseguir validar as rotinas sem depender de
  reiniciar esses serviços.

## Interface e acesso

A camada Laravel deve expor a relação de um `SourceVideo` para seus grupos temáticos em ordem
cronológica. A camada Python deve gravar e ler a mesma representação no PostgreSQL. Nesta entrega,
não é necessário criar uma tela nova; o requisito mínimo é que os dados sejam persistidos e possam
ser consultados pelas camadas existentes.

## Critérios de aceitação

1. Para um vídeo transcrito, o texto completo no banco continua igual ao texto integral recebido.
2. Cada grupo armazena trecho que pode ser reconstruído dos segmentos canônicos, sem texto inventado
   ou omitido.
3. A união dos grupos, na ordem, cobre todos os segmentos não vazios exatamente uma vez; os limites
   temporais correspondem aos segmentos cobertos.
4. Erro, resposta inválida ou indisponibilidade da IA deixa a transcrição consultável e permite
   nova tentativa sem retranscrever quando os dados já estão completos.
5. Reprocessamento não duplica grupos e substitui o conjunto anterior atomicamente.
6. Os sete transcripts existentes de Fabio Akita podem ser organizados sem baixar novamente seus
   vídeos.
7. Vídeos sem transcript completo continuam identificáveis como pendentes de transcrição, não como
   transcrições tematicamente completas.
8. O schema funciona no PostgreSQL existente e é criado pelo fluxo oficial de migrations do projeto.

## Fora de escopo

- Banco dedicado ou armazenamento vetorial.
- Resumos, embeddings, busca semântica e classificação de afirmações.
- Rebaixar ou alterar as prioridades padrão das outras fontes.
- Alterar o seletor de cortes ou usar os grupos temáticos para publicar automaticamente.
- Rebaixar o vídeo bruto como fonte de verdade; a transcrição persistida passa a ser a fonte durável
  para consulta e organização temática.

## Riscos e decisões para implementação

- Vídeos longos podem exceder o limite de contexto. A implementação precisa definir o tamanho e a
  sobreposição dos blocos e validar que a reconciliação cobre todos os segmentos.
- A resposta temática da IA pode vir incompleta ou conter índices inválidos. Deve ser rejeitada
  antes de substituir dados já persistidos.
- O schema e o código de escrita/leitura são compartilhados entre Python e Laravel. A migration,
  modelo e serialização devem manter o mesmo contrato.
- Há alterações paralelas não commitadas no checkout. A implementação deve preservar essas mudanças
  e trabalhar em arquivos/trechos próprios.
