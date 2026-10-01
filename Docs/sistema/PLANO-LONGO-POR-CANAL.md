# Plano — vídeo longo automático, escolhido por canal

**Status:** plano escrito em 01/10/2026, decisões do dono para o futebol e respostas (rampa 6, revezar origem, teto de longos) registradas no mesmo dia; nada implementado.
**Origem:** PR #1 do Ricardo (`release/rico`) fazia todo vídeo gerar Shorts **e** longo, sem chave para
desligar. Recusado como está; o dono quer decidir **por canal destino**, nas configurações do canal.

## Como é hoje (`master`)

O formato é decidido **uma vez por vídeo-fonte**, pela duração (`_detect_format` em
`clip-processor/src/rss_poller.py`):

| Fonte | Formato gravado em `source_videos.format` | O que sai |
|---|---|---|
| menos de 7 min (`MIN_LONGFORM_SECONDS = 420`) | `curto` | até 3 Shorts |
| 7 min ou mais | `longo` | **um** corte contínuo de 7 a 20 min, e **nenhum** Short |

Ou seja: fonte longa vira só longo, fonte curta vira só Shorts. Nunca os dois. A cota do longo já existe
(`MAX_LONGO_UPLOADS_PER_DAY`, padrão 2) e a publicação já reserva horário para ele.

O que **não** existe: o dono não consegue dizer "este canal não quer longo" nem "este canal quer Shorts
**e** longo da mesma fonte".

## O que queremos

Um seletor nas configurações do canal destino, com três modos:

| Modo | Comportamento | Quando usar |
|---|---|---|
| **Automático** (padrão) | Igual a hoje: a duração da fonte decide | Todos os canais, até o dono mudar |
| **Só Shorts** | Fonte longa também gera Shorts, nunca longo | Canal de futebol, se quiser cortar o render e a fila |
| **Shorts + longo** | Fonte com trecho contínuo de 7 min ou mais gera Shorts **e** um longo | Canal de política, se o dono quiser |

**Regra de ouro:** o padrão é "Automático", então **nada muda em produção** até o dono escolher outro
modo num canal. Isso é o que a PR do Ricardo não oferecia.

## Onde guardar a escolha

`destination_channels` já tem `template_config` (JSON) e o padrão de configuração por canal já existe em
mídia (`SISTEMA-MIDIA-POR-CANAL.md`) e perfis de prompt (`PLANO-PROMPTS-EDITAVEIS.md`). Duas opções:

| Opção | Prós | Contras |
|---|---|---|
| **Coluna nova** `destination_channels.long_format_mode` (`auto` \| `short_only` \| `both`) | Simples de consultar em SQL e de validar; migration pequena | Uma migration por opção futura |
| Chave dentro de `template_config` (JSON) | Sem migration | Mistura com configuração de template; sem validação no banco |

**Recomendação:** coluna nova, com default `auto`.

## O ponto difícil: o formato hoje é da fonte, não do canal

`source_videos.format` é gravado na ingestão, **antes** de existir clip. O canal destino só é conhecido
pelo nicho da fonte (`source_channels.target_niche`). Para o modo "Shorts + longo" é preciso gerar dois
conjuntos de clips da mesma fonte. Caminho sugerido:

1. A decisão passa a usar o canal destino do nicho da fonte, lendo `long_format_mode`.
2. `generated_clips.format` (já existe) passa a ser a fonte da verdade do formato **do clip**; o
   `source_videos.format` continua só como padrão. (A PR do Ricardo seguiu esse caminho: painel e cota
   leem o formato do clip, com `format` nulo caindo no formato da fonte.)
3. No modo `both`, o seletor roda **duas vezes** para a mesma fonte (curto e longo), cada uma com seu
   prompt (`SYSTEM_PROMPT` e `LONG_SYSTEM_PROMPT` já existem). O longo só entra se a IA devolver um trecho
   contínuo válido; **sem fallback cego de 13 min**.
4. O raw da fonte só pode ser apagado quando **todos** os clips dela estiverem terminais
   (`_maybe_finalize_source_video` já faz isso; conferir que cobre os dois formatos).

## Riscos e cuidados

- **Disco e render na A1:** `both` dobra o trabalho por fonte. Mexe na janela de download e no bug 12
  (disco). Começar ligando em **um** canal e medir.
- **Cota e fila:** o longo respeita `MAX_LONGO_UPLOADS_PER_DAY`; mais clips = mais itens na aprovação.
  Considerar um teto de longos pendentes por canal.
- **Custo de IA:** duas chamadas de seleção por fonte no modo `both`.
- **Fonte curta no modo `both`:** abaixo de 7 min não há longo; gera só Shorts. Sem erro.
- **Migration antes do código:** a coluna precisa existir antes de o `clip-processor` subir (o `deploy.sh`
  já migra antes de reiniciar, conferir).
- **Fonte longa no modo `short_only`:** hoje fonte longa vira só longo; no novo modo ela precisa gerar
  Shorts a partir do mesmo texto. O seletor de Shorts lê o início da transcrição (corte de caracteres);
  pode ser preciso ampliar a cobertura (item "seletor em janelas" da PR do Ricardo).

## Etapas

1. **Migration + modelo:** coluna `long_format_mode` (default `auto`), validação no painel.
2. **Painel:** campo em *Canais Destino* (select de três opções, com a explicação acima em linguagem simples).
3. **Pipeline:** ler o modo na decisão do formato; `auto` mantém o código atual intacto.
4. **Modo `short_only`:** fonte longa gera Shorts (primeiro modo testável, sem render extra).
5. **Modo `both`:** duas seleções por fonte, clips com `format` próprio.
6. **Testes:** `auto` idêntico ao atual (regressão); cada modo com fonte curta e longa; finalização do raw.
7. **Rollout:** deploy com tudo em `auto`; depois ligar **um** canal, observar render, disco, cota e
   fila por alguns dias antes de ligar o segundo.

## Decisões do dono (01/10/2026)

- **Futebol é o primeiro canal a ligar `both` (Shorts + longo).** É o teste do plano.
- **Mistura do dia: até 10 uploads, 6 Shorts + 4 longos.** Shorts levam mais volume, mas o dono quer
  longos no mix para comparar visualização.
- **Diversificar a origem:** os 10 do dia devem vir de **canais-fonte diferentes**, sem um canal
  dominar a fila.
- **Medir o que dá mais visualização** (por formato e por canal-fonte) em vez de decidir no escuro.
- Contexto: o canal tomou um **strike** e as visualizações ainda não voltaram ao normal (~10 dias).

## O que isso exige no código (verificado em 01/10/2026)

| Necessidade | Hoje | O que muda |
|---|---|---|
| 10 uploads/dia | `ABSOLUTE_MAX_UPLOADS_PER_DAY = 6` em `quota_manager.py` é **teto fixo**; `MAX_UPLOADS_PER_DAY` padrão 2 | Subir o teto absoluto (configurável por ambiente) e a cota do canal |
| 4 longos + 6 Shorts | Só existe teto de longo (`MAX_LONGO_UPLOADS_PER_DAY`, padrão 2) e reserva de vaga quando há longo na fila; **não há teto de Shorts** | Cota por formato: `curto` e `longo` somando no máximo o total |
| Janelas de horário | 12h–14h e 19h–22h (BRT), `LONG_UPLOAD_HOURS` para o longo | Conferir se 10 uploads cabem nessas janelas sem empilhar tudo no mesmo minuto |
| Origens diferentes | A janela de **download** já limita 2 por canal-fonte; a **publicação** não diversifica | Na escolha do próximo clip a publicar, preferir o canal-fonte com menos uploads no dia |
| Ver visualização | O sistema **não coleta views**; só guarda `youtube_video_id` do que publicou | Nova coleta (abaixo) |

### Coleta de métrica (nova)

Um job periódico lê as views dos clips publicados na API do YouTube (`videos.list`, parte `statistics`,
50 ids por chamada, custo mínimo de cota) e grava um histórico: `clip_metrics(clip_id, coletado_em,
views, likes, comentarios)`. Com o clip já ligado a `format` e ao canal-fonte, dá para mostrar no painel:

- views médias por **formato** (Short × longo) nas primeiras 24 h e 7 dias;
- views médias por **canal-fonte**;
- o que nunca passou de algumas dezenas de views.

Depois, o resultado alimenta a prioridade do canal-fonte (`SISTEMA-FRESCOR-E-PRIORIDADE.md` já tem
prioridade por canal-fonte): canal que rende mais ganha mais vaga. Primeiro só **mostrar**; usar para
decidir fica para depois de ter dados.

## Cuidado com o strike

O canal está penalizado e com alcance baixo há ~10 dias. Passar de poucos uploads para 10 por dia de
uma vez muda muito o comportamento do canal e dá pouco sinal sobre o que causou a queda (o strike, o
volume ou o conteúdo). Sugestão, decisão do dono:

1. **Rampa:** começar em ~6/dia (4 Shorts + 2 longos), subir para 10 depois de 1 a 2 semanas estáveis.
2. **Só fontes de baixo risco** de direitos autorais (política do projeto desde 14/09/2026); longo
   contínuo de 7 a 20 min de fonte alheia é o formato de maior exposição.
3. Medir **antes** de subir: sem a coleta de métrica não há como saber se a rampa ajuda ou piora.

## Etapas (ordem revista)

1. Migration `long_format_mode` + campo no painel (padrão `auto`, nada muda).
2. **Coleta de métrica** e tela simples de views por formato e por canal-fonte (valor imediato, zero
   risco para o pipeline).
3. Cota por formato (6 + 4) com teto absoluto configurável; diversificação por canal-fonte na publicação.
4. Modo `both` no seletor (duas seleções por fonte) ligado **só no futebol**.
5. Rollout em rampa (acima), olhando a métrica a cada passo.

Etapas 1 e 2 independem do risco de aumentar volume e podem entrar primeiro.

## Decisões fechadas (01/10/2026)

- **Rampa:** começar em **6 uploads/dia** (4 Shorts + 2 longos) e só subir para 10 depois de 1 a 2 semanas
  estáveis, olhando a métrica.
- **Teto de longos aguardando aprovação por canal:** aprovado (valor inicial sugerido: **4**, igual à
  meta diária de longos; ajustar com o uso).
- **Diversidade de origem:** **só revezar** entre canais-fonte (sem limite fixo por canal-fonte por dia):
  a cada vaga, vai o clip do canal-fonte que publicou há mais tempo.
- **Janela de download não muda por causa deste plano.** Ela conta **vídeos-fonte** (10 por canal destino),
  não clips; o longo e os Shorts da mesma fonte saem do mesmo arquivo e gastam **uma** vaga. Ver
  `Docs/mapas/ideias/longo-e-short-da-mesma-fonte.excalidraw` (mapa visual).

## Disco: o que realmente limita (medido em 01/10/2026)

- A1: `/mnt/videos` com 147 GB, **3,9 GB usados** (3 %); 308 arquivos em `videos/`.
- Com um terceiro canal destino a janela vira 30 vídeos-fonte (3 × 10): o raw é o que pesa e cabe com
  folga. O que encheu o disco no passado foi **fila sem teto** (bug 12) e raw preso, não o tamanho da janela.
- Para crescer sem encher: (1) manter o teto de vídeos-fonte por canal; (2) manter o teto por canal-fonte
  (hoje 2) — é o que reparte a janela; (3) idear **apagar o raw assim que todos os cortes da fonte
  estiverem prontos**, em vez de esperar a aprovação (hoje clip em aprovação segura o raw). Isso só
  vale se nada depois precisar do raw (re-render, censura de palavrão: ver
  `PLANO-REVISAO-DE-PALAVRAO.md`); decidir antes de mudar.

## Decisões em aberto (do dono)

- Nenhuma para a etapa 1 e 2. Para a etapa 4 (modo `both`): confirmar o canal-fonte de teste e a data de
  início da rampa.

Antes de codar: spec curta em `Docs/specs/` (skill `padroes-projeto`), branch `feature/longo-por-canal`.
