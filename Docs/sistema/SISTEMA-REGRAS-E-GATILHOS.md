# Regras operacionais atuais — Canal de Cortes

Este documento descreve os padrões atuais do pipeline. Valores podem ser ajustados por canal ou
no `.env`, conforme indicado.

## Publicação por canal de destino

- O limite padrão é 6 vídeos por dia: até 3 longos e até 3 Shorts.
- Vídeos longos têm três horários diários: 06h, 14h e 22h no fuso `America/Sao_Paulo`, separados
  por oito horas.
- Shorts têm janelas de pico às 12h e 20h. Com esses dois horários, o máximo efetivamente agendado
  é dois Shorts por dia; `SHORTS_PEAK_HOURS` pode receber mais horários se necessário.
- Há no máximo um upload de cada formato por canal em cada horário configurado. A publicação
  depende de fila pronta, quota, aprovação quando exigida, OAuth e disponibilidade do YouTube.

## Frescor das fontes

Cada canal-fonte define no painel se aceita vídeos publicados nos últimos 3 ou 1500 dias.
`FRESHNESS_DAYS=1500` é o fallback para linhas sem configuração. A fila mantém prioridade,
posição configurada e data de publicação.

## Seleção e duração

- Shorts duram de 30 a 45 segundos por padrão. `SHORTS_MAX_DURATION_SECONDS` permite testar um
  limite maior sem mudar o mínimo de 30 segundos.
- Vídeos longos usam um único segmento contínuo de 420 a 1200 segundos (7 a 20 minutos).
- A seleção usa score e regras editoriais por canal; as aprovações do painel dependem de
  `MANUAL_APPROVAL_REQUIRED`.

## Limpeza e histórico pesquisável

Limpeza de disco remove arquivos locais quando eles não são mais necessários. Ela preserva as
linhas de `source_videos` e `generated_clips`, as transcrições (`transcript_text` e
`transcript_data`) e os metadados no PostgreSQL. Os assuntos continuam pesquisáveis para encontrar
novos cortes, inclusive em fontes de pessoas diferentes que abordem o mesmo tema. Cada corte
permanece ligado à sua fonte original.

## Música por canal

Cada música precisa estar associada a um canal de destino no painel ou em
`assets/channels/<slug>/audio/`. O acervo antigo em `assets/audio/` fica preservado como origem e
não é aplicado automaticamente. Shorts não recebem música; o áudio é usado somente em vídeos longos.
