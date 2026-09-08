# Diretório de Documentação (`Docs/`)

Este diretório centraliza toda a documentação, estudos e especificações técnicas do projeto **Canal de Cortes**.

---

## Estrutura de Pastas

```
Docs/
├── sistema/    # Toda a documentação técnica oficial, subsistemas, arquitetura e runbooks
└── estudos/    # Estudos de mercado, pesquisas e mineração de dados (ex: canais de futebol e política)
```

---

## 1. Documentação do Sistema (`Docs/sistema/`)

Contém as especificações operacionais e de engenharia de todos os componentes do sistema:

* [`Docs/sistema/README.md`](sistema/README.md) — Índice geral e mapa completo dos subsistemas.
* [`Docs/sistema/ESTRATEGIA-YOUTUBE-E-BENCHMARK.md`](sistema/ESTRATEGIA-YOUTUBE-E-BENCHMARK.md) — Estratégia de conteúdo, diagnóstico do YouTube Studio, Benchmark de concorrentes e modelo viral de Política (MBL/Missão).
* [`Docs/sistema/BANCO-DE-DADOS.md`](sistema/BANCO-DE-DADOS.md) — Schema, tabelas, suporte híbrido a MySQL/PostgreSQL e rotinas de backup/recuperação (`db:backup`, `db:restore`).
* [`Docs/sistema/SISTEMA-PAINEL.md`](sistema/SISTEMA-PAINEL.md) — Interface web em Laravel 13 + Inertia + React 19, Assistente IA (LLaMA 3.3), Channel Template Studio (9:16), modal de preview de clipes e controles.
* [`Docs/sistema/SISTEMA-CLIP-PROCESSOR.md`](sistema/SISTEMA-CLIP-PROCESSOR.md) — Daemon em Python (21 módulos), ciclo de vida, poller RSS, variáveis de ambiente.
* [`Docs/sistema/SISTEMA-VIDEO.md`](sistema/SISTEMA-VIDEO.md) — Pipeline de vídeo com FFmpeg, enquadramento vertical com fundo desfocado, legendas e thumbnails.
* [`Docs/sistema/SISTEMA-IA-SELECAO.md`](sistema/SISTEMA-IA-SELECAO.md) — Seleção inteligente de cortes por IA (Claude Haiku / Groq LLaMA 3.3).
* [`Docs/sistema/SISTEMA-DOWNLOAD.md`](sistema/SISTEMA-DOWNLOAD.md) — Download via yt-dlp, controle de disco e limpeza automática.
* [`Docs/sistema/SISTEMA-PUBLICACAO.md`](sistema/SISTEMA-PUBLICACAO.md) — Publicação no YouTube, controle de cotas, canais destino e round-robin.
* [`Docs/sistema/SISTEMA-TRANSCRICAO.md`](sistema/SISTEMA-TRANSCRICAO.md) — Transcrição via Groq Whisper API e Transcrição Local com whisper.cpp.
* [`Docs/sistema/SISTEMA-SIDECAR.md`](sistema/SISTEMA-SIDECAR.md) — API interna HTTP na porta 8090 para comunicação com o painel.
* [`Docs/sistema/PIPELINE-E-SCHEDULER.md`](sistema/PIPELINE-E-SCHEDULER.md) — Agendamento de rotinas do daemon e cron jobs.
* [`Docs/sistema/SISTEMA-ALERTAS-E-MONITORAMENTO.md`](sistema/SISTEMA-ALERTAS-E-MONITORAMENTO.md) — Observabilidade em duas camadas: Sentry (crashes), Watchdog proativo (auto-cura de deadlocks e clipes fantasmas) e alertas via Telegram e Email.
* [`Docs/sistema/ESTADOS-E-TRANSICOES.md`](sistema/ESTADOS-E-TRANSICOES.md) — Máquina de estados dos vídeos e clipes.
* [`Docs/sistema/RUNBOOK.md`](sistema/RUNBOOK.md) — Comandos práticos de manutenção, operação e troubleshooting.
* [`Docs/sistema/BUGS.md`](sistema/BUGS.md) — Histórico e backlog de bugs e correções.

---

## 2. Estudos e Pesquisas (`Docs/estudos/`)

Contém análises, pesquisas de canais, dados de mineração e benchmarks de conteúdo:

* `Docs/estudos/mineracao_canis.xlxs` — Planilha com mapeamento, métricas e mineração de canais fonte e concorrentes no YouTube.
