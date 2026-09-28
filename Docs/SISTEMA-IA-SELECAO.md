# IA e catálogo de prompts

> Tipo: referência as-built · Atualizado: 2026-08-27
> Fontes: `clip-processor/src/prompt_profiles.py`, `selector.py`,
> `metadata_generator.py`, `video_processor.py` e migrations do painel

O texto editorial específico vive em `prompt_profiles` no PostgreSQL. O painel associa um perfil
ativo a cada canal-fonte e canal-destino. Regras de segurança, fact-check, contrato JSON,
anti-repetição e pós-validação continuam no código e são aplicadas a todos os perfis.

Não há editor livre de prompts nem versionamento por usuário: novos perfis são adicionados por
migration/seeder idempotente, revisados em código e associados aos canais no painel.

## Roteamento

O nicho é lido de `source_channels.target_niche` ou `destination_channels.niche`; o perfil é
resolvido pela FK `prompt_profile_id`. O perfil precisa estar ativo e ser compatível por `slug`,
`niche` ou `niche_aliases`. Um perfil explícito incompatível é rejeitado pelo painel.

| Origem | Perfil usado | Etapa |
|---|---|---|
| canal-fonte | `source_channels.prompt_profile_id` | seleção de momentos |
| canal-destino | `destination_channels.prompt_profile_id` | metadata e thumbnail |
| publicação | mesmo perfil da fonte, quando existe | escolha do destino |

Quando uma fonte legada ainda não tem perfil, o sistema usa somente o fallback por nicho já
existente; nicho ausente ou desconhecido usa instrução genérica, nunca o perfil editorial de outro
nicho. Se o destino não tiver o mesmo perfil de uma fonte configurada, o clip fica sem destino em
vez de atravessar a fronteira editorial.

| `fmt` | Seleção | Metadata |
|---|---|---|
| `curto` | prompt curto da família escolhida | prompt curto da família escolhida |
| `longo` | prompt longo da família escolhida | prompt longo da família escolhida |

## Perfis semeados

Migration [`2026_08_27_000000_create_prompt_profiles_table.php`](../painel/database/migrations/2026_08_27_000000_create_prompt_profiles_table.php)
cria/atualiza três perfis idempotentes:

| Slug | Nicho canônico | Foco |
|---|---|---|
| `futebol` | `futebol` | futebol brasileiro/internacional e esporte |
| `conteudo-inteligencia` | `hacker-libertario` | IA, tecnologia, Linux, Open Source, cibersegurança, criptografia e soberania digital libertária (anti-estatista, zero menções a políticos) |
| `podcast` | `podcast` | entrevistas, histórias, opiniões e debates |

> **Diretrizes Libertárias do Perfil `conteudo-inteligencia`:**
> 1. **O Estado nunca deve ser defendido:** Rejeita qualquer defesa, elogio ou legitimação de tributação, regulação estatal, censura ou intervenção estatal. Trechos sobre regulação ou vigilância só são aceitos quando a abordagem for crítica e apontar soluções de defesa individual por meio de tecnologia e criptografia.
> 2. **Zero menções a políticos ou funcionários públicos:** Proibição absoluta de citar nomes de políticos (de qualquer partido) ou burocratas/agentes estatais no título, descrição, tags ou recortes. O foco é 100% nas ideias, ferramentas, tecnologia, privacidade e liberdade individual.
> 3. **Gancho viral imediato (0 a 3s):** O corte começa no auge da afirmação de impacto, eliminando saudações e pausas.

Cada perfil possui cinco campos de prompt: `selection_short_prompt`, `selection_long_prompt`,
`metadata_short_prompt`, `metadata_long_prompt` e `thumbnail_prompt`. Para criar outro nicho em
uma instalação existente, crie uma migration/seed de dados idempotente com os cinco campos e seus
aliases, inclua o nicho na tabela `niches` e associe os canais ao novo `prompt_profile_id`. Não edite
uma migration já aplicada esperando que ela seja executada novamente.

## Providers atuais

| Etapa | Anthropic | Groq | Comportamento |
|---|---|---|---|
| seleção | `claude-haiku-4-5`, quando há chave | `openai/gpt-oss-20b` | Anthropic → Groq em produção |
| metadata | `claude-haiku-4-5`, quando há chave | `openai/gpt-oss-20b` | provider escolhido pela configuração; sem fallback cruzado |
| thumbnail | `claude-haiku-4-5`, quando há chave | `openai/gpt-oss-20b` | provider escolhido pela configuração; sem fallback cruzado |
| transcrição | — | `whisper-large-v3-turbo` | não usa prompt de linguagem natural |

A seleção usa temperatura 0,3, raciocínio `low` e até 2.048 tokens. Metadata usa
temperatura 0,3 e até 2.048 tokens no Groq. A chamada da thumbnail usa temperatura 0,2 e até
512 tokens no Groq.

Com `ANTHROPIC_API_KEY` vazia, seleção, metadata e thumbnail usam Groq diretamente. Se
metadata ou thumbnail falharem, o clip falha; metadata não possui fallback determinístico e
thumbnail não possui fallback local.

## Prompts compartilhados da seleção

### `CONTENT_SELECTION_RULES`

Contrato editorial comum a todas as quatro seleções:

- ler todos os segmentos temporizados antes de escolher;
- detectar semanticamente publicidade, patrocínio, merchandising, product placement, ofertas,
  cupons, códigos, CTAs, links e QR codes;
- excluir o bloco comercial completo, incluindo transições, sem posição ou duração fixa;
- distinguir menção editorial de publicidade quando não há promoção;
- escolher assunto com começo, contexto, desenvolvimento e conclusão;
- iniciar após o setup necessário e terminar depois da resposta/desfecho, em pausa ou troca de assunto;
- nunca cortar palavra, frase, pergunta, resposta, explicação, história, piada, raciocínio,
  conjunção ou preposição;
- não forçar duração: se o assunto completo não couber, descartar;
- não atravessar o marcador `[...]` de trecho omitido;
- tratar timestamps como blocos, não como garantia de fim de frase;
- ler linhas seguintes e estender `end_time` até pontuação, pausa ou troca de assunto.

### `DUPLICATE_AVOIDANCE_RULE`

Recebe o histórico de intervalos já registrados para a mesma fonte. Todos os intervalos são
bloqueados; nova seleção não pode reutilizar material nem sobrepor mais de 0,5 s. Tema parecido,
sozinho, não é duplicidade. Se todos os candidatos estiverem bloqueados, retorna lista vazia.

### `SELECTION_VALIDATION_RULES`

Pede releitura até `end_time` e da continuação imediata. O modelo deve confirmar início
natural e fechamento da ideia; se não confirmar sem atravessar lacuna ou publicidade, descarta.

## Prompts de seleção

| Constante | Família/formato | Finalidade |
|---|---|---|
| `SYSTEM_PROMPT` | futebol/podcast, curto | até 3 momentos de 30 s exatos; prioriza análise tática, debate, bastidores, gol, revelação, conflito ou humor |
| `LONG_SYSTEM_PROMPT` | futebol/esportes, longo | exatamente 1 segmento contínuo de 420–1200 s; análise, entrevista ou debate completo |
| `HACKER_LIBERTARIO_PROMPT` | tecnologia, curto | até 3 momentos de 30 s exatos; IA, Linux, Open Source, programação, segurança, privacidade, soberania e carreira |
| `HACKER_LIBERTARIO_LONG_PROMPT` | tecnologia, longo | exatamente 1 segmento contínuo de 420–1200 s; explicação técnica, soberania ou debate aprofundado |

Cada prompt de seleção concatena as três regras compartilhadas, `FACT_CHECK_INSTRUCTION`
e um contrato JSON. O curto pede no máximo 3 itens ordenados por score; o longo pede exatamente
1 item. O score esperado é de 1 a 10. Com perfil ativo, o texto específico vem de
`selection_short_prompt`/`selection_long_prompt`; as quatro constantes acima são fallback de
compatibilidade para canais legados.

Contrato de saída:

~~~json
{
  "moments": [
    {
      "start_time": 0,
      "end_time": 60,
      "score": 8,
      "reason": "motivo editorial; termina com Fake news: negativo",
      "fake_news": "negativo"
    }
  ]
}
~~~

## Verificação factual da seleção

`FACT_CHECK_INSTRUCTION` manda pesquisar na internet quando houver fato, data, número,
nome, estatística, declaração ou alegação verificável; usar fonte confiável e, quando possível,
uma segunda fonte; nunca inventar fonte, URL ou resultado.

`FAKE_NEWS_STATUSES` aceita:

| Valor | Significado |
|---|---|
| `positivo` | há evidência de informação falsa, enganosa ou fora de contexto |
| `negativo` | fontes confiáveis corroboram a informação |
| `inconclusivo` | evidência insuficiente ou pesquisa indisponível |

O campo `reason` deve terminar exatamente com `Fake news: <status>`. A
normalização Python também corrige labels e escala de score 0–1 para 0–10.

## Entrada e pós-validação da seleção

A transcrição vira linhas no formato `[123s-150s] texto`. A entrada é limitada para
respeitar a cota do Groq:

- curto: 8.000 caracteres;
- longo: 14.000 caracteres, preservando início e últimos 3.000 caracteres;
- entre as duas partes longas entra `[... trecho intermediário omitido ...]`, que é uma
  lacuna proibida para seleção.

O histórico do vídeo é anexado depois da transcrição. Após a resposta da IA, Python:

1. limita tempos à duração conhecida;
2. completa bordas de fala;
3. expande contexto do longo;
4. remove material repetido e overlaps;
5. aplica quantidade máxima (3 curto, 1 longo);
6. aplica duração (curto 30 s exatos; longo 420–1200 s);
7. insere somente momentos com score mínimo 7.

O campo `generated_clips.reason` preserva o motivo e a classificação factual. A inserção
é idempotente contra intervalos já usados.

## Limitação conhecida

O prompt curto prevê exceção para fonte com menos de 30 s, mas a chamada final de
`_filter_shortform_duration` não recebe `transcript_duration`. Portanto, o
filtro Python pode descartar um candidato curto abaixo de 30 s mesmo quando a fonte inteira é
menor. Qualquer ajuste deve alterar prompt, filtro e testes juntos.

## Prompts de metadata

### `HACKER_CHANNEL_SEO_INSTRUCTION`

Aplicada aos nichos de tecnologia. Define a identidade Hacker Libertário, exige palavra-chave
técnica específica, resumo inicial, contexto da transcrição, CTA curto e no máximo três hashtags
relevantes. Tags misturam termos amplos/específicos, sem `#`, duplicatas ou termos fora do
trecho. Créditos são adicionados pelo código depois.

### `METADATA_EDITORIAL_INSTRUCTION`

É compartilhada por metadata de futebol e tecnologia:

- criar título novo, específico e editorial;
- usar título original somente como contexto, nunca copiá-lo;
- descrever contexto, argumentos e conclusão em PT-BR;
- usar somente transcrição/contexto;
- não inventar fatos;
- não inserir `Shorts`, `corte`, `Vídeo longo` ou duração no título;
- não escrever créditos;
- não produzir `@@`.

### `METADATA_FACT_CHECK_INSTRUCTION`

É anexada aos quatro prompts de metadata e também ao prompt enviado em cada chamada. Quando
houver alegação verificável, exige pesquisa em fontes confiáveis; se não houver ferramenta web,
proíbe declarar que a pesquisa foi feita. Os status negativo e inconclusivo nunca aparecem na
descrição. Somente o status positivo acrescenta, após duas quebras de linha, `Fact Check:` seguido
dos fatos reais; na ausência de detalhes adicionais, o fallback é `Fact Check: E os fatos reais.`.

### Famílias

| Constante | Formato | Finalidade |
|---|---|---|
| `SYSTEM_PROMPT` | futebol, curto | SEO de Shorts sobre futebol; título até 100 caracteres, descrição contextual e tags de tema |
| `LONG_SYSTEM_PROMPT` | futebol, longo | SEO de vídeo horizontal; sem tags `Shorts` ou `cortes` |
| `HACKER_LIBERTARIO_SYSTEM_PROMPT` | tecnologia, curto | SEO de Shorts/cortes técnicos com identidade Hacker Libertário |
| `HACKER_LIBERTARIO_LONG_SYSTEM_PROMPT` | tecnologia, longo | SEO de vídeo horizontal técnico; sem `Shorts` ou `cortes` |

Todos concatenam a instrução editorial e `METADATA_FACT_CHECK_INSTRUCTION`.

Com perfil ativo, metadata usa `metadata_short_prompt` ou `metadata_long_prompt` do canal-destino;
`HACKER_CHANNEL_SEO_INSTRUCTION` e as constantes de família permanecem apenas como fallback para
canais legados. O `thumbnail_prompt` do mesmo perfil é aplicado separadamente à chamada textual da
thumbnail.

O builder `_build_prompt` envia perfil, formato, nicho, título original, motivo, score, intervalo,
trecho da transcrição e contrato de saída. O contrato é:

~~~json
{
  "title": "título editorial",
  "description": "descrição em PT-BR",
  "tags": ["termo 1", "termo 2"]
}
~~~

A normalização Python rejeita título vazio, original, maior que 100 caracteres ou com rótulo
genérico; exige descrição e tags, remove hashtags/duplicatas e remove tags de Shorts/cortes em
vídeos longos. O veredito factual só vira uma linha `Fact Check:` quando for positivo; status
negativo e inconclusivo são omitidos da descrição.

## Prompt de thumbnail

### `THUMBNAIL_SYSTEM_PROMPT`

A chamada deve maximizar clareza e CTR usando conflito, surpresa, contradição, revelação, pergunta
ou afirmação inesperada, mas ser uma sequência contínua realmente dita no trecho. Não pode
parafrasear, intensificar, completar, inventar acusação nem usar informação externa.

O builder `_build_thumbnail_prompt` fornece o `thumbnail_prompt` do perfil, título original,
motivo, score, formato e transcrição apenas como contexto; ordena resposta JSON única:

~~~json
{"thumbnail_text": "frase literal"}
~~~

Regras Python:

- entre 2 e 10 palavras;
- no máximo 64 caracteres;
- deve ser substring literal do trecho após normalização de acentos/pontuação;
- não pode ser vazio;
- não é persistido em `generated_clips`; é aplicado na imagem.

O sistema seleciona Anthropic se a chave existir, caso contrário Groq. Resposta inválida ou frase
não literal lança erro e marca o clip como `failed`.

## Instruções que não são prompts de LLM

- `youtube_oauth.py` usa `prompt='consent'` no OAuth; é parâmetro do Google,
  não prompt de IA.
- Whisper recebe idioma e parâmetros de áudio, mas não recebe prompt textual.
- `youtube/assets/BRANDING.md` é guia de identidade/SEO manual; suas regras são referência
  de marca, não são concatenadas automaticamente ao system prompt.
- testes em `clip-processor/tests/test_selector.py` e
  `test_metadata_generator.py` verificam contratos; não são prompts de produção.

## Fonte de verdade

Ao alterar um perfil, atualize a seed/migration de dados, o teste correspondente e este catálogo. Confira
sempre `GROQ_CHAT_MODEL` em ambos os módulos; a configuração atual é `openai/gpt-oss-20b`.
Não use descrições antigas que mencionem LLaMA 3.3/70B, 120B, metadata determinística ou editor de
prompts como se fossem runtime.
