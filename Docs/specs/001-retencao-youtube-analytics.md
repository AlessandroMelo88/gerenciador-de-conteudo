# SPEC-001 — Retenção do YouTube Analytics por clip

**Status:** Rascunho
**Data:** 02/10/2026
**ADRs relacionados:** ADR-0004 (fallback de IA obrigatório), ADR-0005 (schema evolui por migration guardada)
**Onde vive o código:** `clip-processor/src/` (coleta) e `painel/` (migration e leitura)

## 1. Objetivo

O `selector.py` pontua trechos de 0 a 10 e nunca descobre o que aconteceu depois da publicação: o ciclo
de aprendizado está aberto. Esta spec é a **etapa 1 de 3** do fechamento desse ciclo — trazer para o banco
a retenção real de cada clip publicado (`averageViewPercentage` da YouTube Analytics API), que é a única
métrica que mede o que o seletor de fato decide: se o **trecho** escolhido é bom.

Etapas 2 e 3, fora desta spec: um LLM lê os extremos de retenção e propõe hipótese em uma frase; o dono
aprova no painel; a hipótese aprovada entra na camada de prompt do seletor.

Liga-se a "Para onde vamos" pela qualidade do conteúdo próprio: clip que retém mais sustenta canal e
oferta de afiliado sem depender da monetização do YouTube.

## 2. Fora de escopo

- Gerador de hipótese, fila de aprovação e injeção no prompt do seletor (etapas 2 e 3).
- Tela nova no painel. A retenção aparece nas seções que **já existem** em `/painel/metricas`.
- Mexer na tabela `clip_metrics` ou no `metrics_collector.py`. Continuam como estão.
- CTR, impressões e fontes de tráfego. A chamada traz outras métricas de graça, mas nenhuma decisão
  desta spec depende delas.
- Qualquer coleta no painel Laravel. A credencial do YouTube é do clip-processor e continua só lá.

## 3. Regras de negócio

**Dados**

- **R1.** A coleta grava em `clip_daily_metrics`, com grão **clip × dia**. Chave única
  `(generated_clip_id, date)`.
- **R2.** A gravação é **upsert**: coletar o mesmo dia duas vezes atualiza a linha, nunca duplica. O
  YouTube revisa o dado de um dia depois de fechá-lo, e a última leitura é a que vale.
- **R3.** A FK para `generated_clips` tem `ON DELETE CASCADE`, como a de `clip_metrics`: medição é filho
  descartável e apagar um clip nunca pode falhar por causa dela.
- **R4.** `average_view_percentage` é a nota de retenção do clip. É a coluna que as etapas 2 e 3 consomem.

**OAuth**

- **R5.** `youtube_oauth.py` passa a pedir também `https://www.googleapis.com/auth/yt-analytics.readonly`,
  junto dos escopos que já existem (`youtube.upload`, `youtube.force-ssl`).
- **R6.** Token sem o escopo novo **não** quebra nada: a chamada falha, o erro é logado e o ciclo segue.
  Publicação e todo o resto do pipeline seguem funcionando com o token antigo. Isso permite o deploy do
  código antes da re-autorização dos canais.

**Coleta**

- **R7.** O coletor novo é `clip-processor/src/retention_collector.py`, irmão do `metrics_collector.py`,
  e **nenhuma** exceção dele propaga: falha de API, de rede ou de banco é logada e o ciclo segue
  (regra do projeto: melhoria de qualidade jamais vira indisponibilidade).
- **R8.** `RETENTION_COLLECTOR_ENABLED` (padrão ligado) desliga o job sem mexer no resto, no padrão do
  `METRICS_COLLECTOR_ENABLED`.
- **R9.** Roda **uma vez por dia**. A Analytics API consolida por dia; coletar de hora em hora só gasta cota.
- **R10.** Teto de chamadas por canal por dia em `RETENTION_MAX_CALLS_PER_CHANNEL_DAY` (padrão 200). Teto
  atingido interrompe o canal e retoma no dia seguinte.
- **R11.** Só entram clips com `status = 'published'` e `youtube_video_id` preenchido.
- **R12.** A janela de coleta de um clip vai da data de publicação até 30 dias depois, alinhada ao
  `STOP_DAYS` do `metrics_collector.py`. Clip mais velho não é mais consultado.
- **R13.** A resposta é lida por `columnHeaders`, nunca por posição de coluna.
- **R14.** Clip sem linha na resposta (vídeo apagado, privado, ou sem audiência no dia) é contado no log
  e ignorado, sem gravar linha zerada.

**Backfill**

- **R15.** A carga retroativa é um comando separado (`python -m src.retention_backfill`), rodado à mão,
  que coleta de cada clip publicado desde a sua data de publicação. Não é agendado e não compartilha
  caminho de código com o job diário, para não misturar carga histórica com operação.

**Painel**

- **R16.** Em `/painel/metricas`, "Qual canal de origem rende mais" passa a ordenar por retenção média
  e "Clips que não pegaram" passa a exibir o percentual assistido. O recorte de tempo é **o mesmo que a
  tela já usa hoje**; esta spec não introduz filtro de período novo.
- **R17.** Sem dado de retenção (antes do backfill, ou canal sem o escopo novo), a tela mostra os números
  de hoje e indica a ausência; não quebra nem mostra zero como se fosse medição.

## 4. Contrato

### Tabela `clip_daily_metrics`

Migration em `painel/database/migrations/`, guardada por `Schema::hasTable` (ADR-0005).

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | bigint PK | |
| `generated_clip_id` | FK `generated_clips` | `cascadeOnDelete` (R3) |
| `date` | date | dia do relatório, em UTC como a API devolve |
| `views` | bigint | |
| `estimated_minutes_watched` | bigint | |
| `average_view_duration` | integer | segundos |
| `average_view_percentage` | decimal(5,2) | **a nota de retenção** (R4) |
| `likes` | bigint nullable | |
| `comments` | bigint nullable | |
| `shares` | bigint nullable | |
| `subscribers_gained` | bigint nullable | |

Índices: único em `(generated_clip_id, date)`; índice em `date`.

### Chamada à Analytics API

`POST https://youtubeanalytics.googleapis.com/v2/reports`

```
ids=channel==MINE
startDate=<publicação do clip mais antigo da leva>
endDate=<ontem>
dimensions=video,day
metrics=views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained
filters=video==<id>,<id>,...
```

`channel==MINE` porque o token já é do canal destino; `channel==<id>` exigiria conta de content owner.
Resposta mapeada por `columnHeaders` (R13).

### Variáveis de ambiente

| Variável | Padrão | O que faz |
|---|---|---|
| `RETENTION_COLLECTOR_ENABLED` | `true` | desliga o job (R8) |
| `RETENTION_MAX_CALLS_PER_CHANNEL_DAY` | `200` | teto de chamadas (R10) |

Precisam entrar no `environment:` do `clip-processor` em `docker-compose.yml`, senão não chegam ao
container (armadilha registrada em 01/10/2026).

## 5. Critérios de pronto

- [ ] Cada regra da §3 tem teste
- [ ] `tests/test_retention_collector.py` cobre: resposta normalizada, `columnHeaders` fora de ordem,
      vídeo sem dado (R14), escopo insuficiente (R6), teto de cota (R10), upsert do mesmo dia (R2)
- [ ] `pytest` dentro da imagem `wordpress-clip-processor` passando
- [ ] `php artisan test` do painel passando contra PostgreSQL
- [ ] `vendor/bin/pint` limpo
- [ ] `Docs/sistema/` atualizado (coletor novo e tabela nova) e `Docs/PROGRESSO.md` com a etapa 1
- [ ] Esta spec em **Entregue**

## 6. Riscos e perguntas em aberto

| Item | Dono | Estado |
|---|---|---|
| Re-autorizar os 2 canais no Google com o escopo novo e levar os `token-{slug}.json` ao servidor | Dono | Pendente — o código vai a produção antes, por R6 |
| Cota da Analytics API (projeto GCP de cada canal) com o backfill de ~141 clips | Claude | A medir no backfill; R10 limita o estrago |
| Shorts podem reportar `averageViewPercentage` de forma diferente de vídeo longo | Claude | Conferir na primeira leva real antes da etapa 2 |
| Volume baixo (~141 clips) pode não sustentar hipótese estatística | Dono | Aceito: a etapa 2 usa LLM lendo extremos, não estatística |
