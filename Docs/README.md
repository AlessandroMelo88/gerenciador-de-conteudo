# Docs — mapa da documentação

Este é o índice. Em dois minutos dá para saber **onde está cada tipo de documento**, **em que estado ele
está** e **o que falta fazer**.

> **Quer saber o que foi feito e o que falta?** Abra [`PROGRESSO.md`](PROGRESSO.md).
> **Quer saber onde paramos e para onde vamos?** Abra [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md).

---

## Pastas, por tipo de documento

```
Docs/
├── PROGRESSO.md            # painel: FEITO / EM ANDAMENTO / IDEIA / PENDÊNCIA / OBSOLETO (leia primeiro)
├── ESTADO-DO-PROJETO.md    # checkpoint curto: produção, decisões, em aberto, próximo passo
├── sistema/                # COMO FUNCIONA (referência as-built, vigente)
├── operacao/               # COMO OPERAR (runbook, bugs, lint/testes/CI)
├── planos/                 # O QUE SE PLANEJOU (planos, ideias, migrações) — cada um com **Status:** no topo
├── specs/                  # O QUE UMA FEATURE FAZ e como saber que ficou pronta (regras numeradas e testáveis)
├── adr/                    # POR QUE FOI DECIDIDO ASSIM (decisões de arquitetura)
├── estudos/                # PESQUISA (estratégia de conteúdo, planilhas de mineração de canais)
├── mapas/                  # diagramas (mapa.excalidraw)
└── historico/              # ARQUIVO: obsoleto ou superado, preservado e nunca apagado
```

Estados usados nos cabeçalhos: **VIGENTE** · **FEITO** (plano concluído e no ar) · **EM ANDAMENTO** ·
**IDEIA** (escrita, não implementada) · **OBSOLETO** (superado; só histórico).

Documentos fora de `Docs/` que fazem parte do conjunto: [`../README.md`](../README.md) (visão geral),
[`../ARCHITECTURE.md`](../ARCHITECTURE.md) (arquitetura as-built), [`../DEPLOY.md`](../DEPLOY.md) (deploy e
regra de branch), [`../CONTRIBUTING.md`](../CONTRIBUTING.md), [`../CLAUDE.md`](../CLAUDE.md) (regras
destrutivas e armadilhas), [`../CHANGELOG.md`](../CHANGELOG.md).

---

## Como funciona — `sistema/` (vigente)

Índice com uma linha por documento: [`sistema/README.md`](sistema/README.md). Os principais:

| Documento | Estado | Em uma linha |
|---|---|---|
| [`sistema/SISTEMA-CLIP-PROCESSOR.md`](sistema/SISTEMA-CLIP-PROCESSOR.md) | VIGENTE | Mapa módulo a módulo do daemon Python |
| [`sistema/PIPELINE-E-SCHEDULER.md`](sistema/PIPELINE-E-SCHEDULER.md) | VIGENTE | Jobs, cadências e o que cada ciclo faz |
| [`sistema/ESTADOS-E-TRANSICOES.md`](sistema/ESTADOS-E-TRANSICOES.md) | VIGENTE | Máquina de estados e recuperação automática |
| [`sistema/SISTEMA-DOWNLOAD.md`](sistema/SISTEMA-DOWNLOAD.md) | VIGENTE | RSS, dedup, janela e frescor de download |
| [`sistema/SISTEMA-FRESCOR-E-PRIORIDADE.md`](sistema/SISTEMA-FRESCOR-E-PRIORIDADE.md) | VIGENTE | Janela e prioridade por canal-fonte |
| [`sistema/SISTEMA-TRANSCRICAO.md`](sistema/SISTEMA-TRANSCRICAO.md) | VIGENTE | Transcrição do pipeline e base de conhecimento (extensão, Hotmart) |
| [`sistema/SISTEMA-BUSCA-TRANSCRICOES.md`](sistema/SISTEMA-BUSCA-TRANSCRICOES.md) | VIGENTE | Busca texto/semântica/híbrida, pgvector, embedder |
| [`sistema/SISTEMA-IA-SELECAO.md`](sistema/SISTEMA-IA-SELECAO.md) | VIGENTE | Escolha dos cortes por IA, com fallback Groq |
| [`sistema/SISTEMA-VIDEO.md`](sistema/SISTEMA-VIDEO.md) | VIGENTE | FFmpeg: corte, legenda, thumbnail |
| [`sistema/SISTEMA-MIDIA-POR-CANAL.md`](sistema/SISTEMA-MIDIA-POR-CANAL.md) | VIGENTE | Intro, encerramento e música por canal |
| [`sistema/SISTEMA-PUBLICACAO.md`](sistema/SISTEMA-PUBLICACAO.md) | VIGENTE | Roteamento, cota, janela e OAuth do YouTube |
| [`sistema/SISTEMA-SIDECAR.md`](sistema/SISTEMA-SIDECAR.md) | VIGENTE | API interna painel ↔ pipeline (porta 8090) |
| [`sistema/SISTEMA-PAINEL.md`](sistema/SISTEMA-PAINEL.md) | VIGENTE | Rotas, controllers e telas do painel |
| [`sistema/BANCO-DE-DADOS.md`](sistema/BANCO-DE-DADOS.md) | VIGENTE | Schema, backup e restauração |
| [`sistema/SISTEMA-ALERTAS-E-MONITORAMENTO.md`](sistema/SISTEMA-ALERTAS-E-MONITORAMENTO.md) | VIGENTE | Better Stack, Sentry, watchdog, Telegram |
| [`sistema/SISTEMA-AFILIADOS.md`](sistema/SISTEMA-AFILIADOS.md) | VIGENTE | Ofertas, link rastreável, Telegram, tema Umbrella |
| [`sistema/SISTEMA-REGRAS-E-GATILHOS.md`](sistema/SISTEMA-REGRAS-E-GATILHOS.md) | VERIFICAR | Resumo antigo de metas e janelas; contradiz o código |

## Como operar — `operacao/`

| Documento | Estado | Em uma linha |
|---|---|---|
| [`operacao/GUIA-CRIACAO-CANAL-YOUTUBE.md`](operacao/GUIA-CRIACAO-CANAL-YOUTUBE.md) | VIGENTE | Passo a passo completo: YouTube Studio, OAuth, GCP, token e automação |
| [`operacao/RUNBOOK.md`](operacao/RUNBOOK.md) | VIGENTE | Comandos do dia a dia, destrave de estado preso, reinício seguro |
| [`operacao/BUGS.md`](operacao/BUGS.md) | VIGENTE | Backlog de bugs com status e evidência (abertos: 6, 8, 10) |
| [`operacao/DESENVOLVIMENTO.md`](operacao/DESENVOLVIMENTO.md) | VIGENTE | Lint, testes e CI (`make help`) |

## Planos e migrações — `planos/`

Cada arquivo tem `**Status:**` com data no topo. O resumo por estado está em [`PROGRESSO.md`](PROGRESSO.md).

| Documento | Estado | Em uma linha |
|---|---|---|
| [`planos/PLANO-MESTRE.md`](planos/PLANO-MESTRE.md) | EM ANDAMENTO | Direitos autorais, A1+PostgreSQL, Umbrella, afiliados e ordem de execução |
| [`planos/MIGRACAO-A1.md`](planos/MIGRACAO-A1.md) | FEITO (17/09/2026) | Como ficou a produção na VM A1, rollback e pendências |
| [`planos/PLANO-POSTGRES.md`](planos/PLANO-POSTGRES.md) | FEITO | Fases A e B da troca de MySQL para PostgreSQL |
| [`planos/PLANO-PROMPTS-EDITAVEIS.md`](planos/PLANO-PROMPTS-EDITAVEIS.md) | IDEIA | Editar prompts da IA pelo painel, com métricas |
| [`planos/PLANO-REVISAO-DE-PALAVRAO.md`](planos/PLANO-REVISAO-DE-PALAVRAO.md) | IDEIA | Palavrão com minutagem e escolha por clip antes de publicar |
| [`planos/PLANO-LONGO-POR-CANAL.md`](planos/PLANO-LONGO-POR-CANAL.md) | IDEIA | Vídeo longo automático escolhido por canal destino |
| [`planos/CI-CD.md`](planos/CI-CD.md) | IDEIA | Deploy automático diário (só desenho) |

## Decisões — `adr/`

[`adr/README.md`](adr/README.md): ADRs 0001 a 0007 (busca vetorial, compose isolado, fila no banco, fallback
de IA, schema fora das migrations, ferramentas de qualidade, PostgreSQL 17).

## Estudos e mapas — `estudos/`, `mapas/`

| Arquivo | Em uma linha |
|---|---|
| [`estudos/ESTRATEGIA-YOUTUBE-E-BENCHMARK.md`](estudos/ESTRATEGIA-YOUTUBE-E-BENCHMARK.md) | Estratégia de conteúdo, métricas do YouTube Studio, benchmark e modelo de cortes de política |
| `estudos/mineracao_canis.xlxs` | Planilha de mineração de canais-fonte e concorrentes (extensão `.xlxs` é typo antigo; abre como xlsx) |
| `estudos/Outlier_Multilingue.xlsx` | Planilha de outliers multilíngue |
| `mapas/mapa.excalidraw` | Diagrama de arquitetura em Excalidraw |

## Arquivo — `historico/` (obsoleto ou superado)

| Documento | Estado | Por que está aqui |
|---|---|---|
| [`historico/PLANO-ORACLE.md`](historico/PLANO-ORACLE.md) | OBSOLETO | Plano de migração para a Oracle com MySQL; superado pela migração real (MIGRACAO-A1) |
| [`historico/RETOMADA-TRANSCRICOES.md`](historico/RETOMADA-TRANSCRICOES.md) | ARQUIVADO | Passagem de contexto de 18/09/2026; superada pelo checkpoint |
| [`historico/RETOMADA-SESSAO-CRON.md`](historico/RETOMADA-SESSAO-CRON.md) | OBSOLETO | Agendamento pontual de 15/09/2026 após limite de uso do Claude Code |
| [`historico/ESTADO-AGOSTO-2026.md`](historico/ESTADO-AGOSTO-2026.md) | OBSOLETO | Retrato "estado atual" de agosto, retirado do índice de `sistema/` |

---

## Como manter

- Status mora no documento: mudou o estado de um plano, atualize o `**Status:**` dele **e** a linha em
  [`PROGRESSO.md`](PROGRESSO.md).
- Ao fim de cada rodada, atualize [`ESTADO-DO-PROJETO.md`](ESTADO-DO-PROJETO.md) (curto; não duplique o PROGRESSO).
- Moveu ou renomeou um documento: `python3 scripts/check-doc-links.py` tem que acabar com 0 quebrados.
- Um plano que foi concluído continua em `planos/` com status FEITO; só vai para `historico/` quando fica
  obsoleto (superado por outra coisa).
