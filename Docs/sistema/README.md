# Docs — Sistema Canal de Cortes

Índice da documentação técnica do sistema. **Comece por aqui em toda conversa nova.**

Última atualização: **Setembro/2026**

---

## O que o sistema é, em um parágrafo

Pipeline automatizado que monitora canais no YouTube via RSS, corta os melhores momentos com
IA e publica nos canais próprios. O fluxo é **100% automático** por default, da descoberta ao upload. O
painel web existe para **observar, configurar templates e intervir**, não para operar o fluxo manual.

Dois serviços principais: `clip-processor` (daemon Python, faz todo o trabalho de pipeline) e `painel` (Laravel 13 + Inertia 3 +
React 19, interface administrativa, estúdio de templates e rotinas de backup). Dois formatos de saída, decididos pela duração do vídeo fonte: **`curto`**
(fonte < 7 min ⇒ até 3 shorts verticais de 30 s a 3 min com enquadramento adaptativo ou blur background) e **`longo`** (fonte ≥ 7 min ⇒ um corte
horizontal de 7 a 20 min).

---

## Onde está cada coisa

### Ponto de partida

| Documento | Responde |
|---|---|
| [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) | Arquitetura as-built: topologia dos containers, a fronteira painel ↔ pipeline, decisões e dívida técnica. **Primeira leitura de quem chega agora** |
| [`../../CLAUDE.md`](../../CLAUDE.md) | As 7 regras de operação destrutiva e os incidentes que as geraram. **Ler antes de apagar qualquer coisa** |
| [`RUNBOOK.md`](RUNBOOK.md) | Comandos do dia a dia: está de pé? por que parou? como reiniciar sem travar clip? como limpar disco em duas etapas? |
| [`BUGS.md`](BUGS.md) | Backlog com status FEITO / PARCIAL / ABERTO / SUSPEITA, evidência e onde corrigir |

### Como o sistema funciona, por subsistema

| Documento | Responde |
|---|---|
| [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md) | Máquina de estados de `source_videos` e `generated_clips`, quem escreve cada transição, **o que tem e o que não tem recuperação automática**, e o que ocupa vaga na janela de download |
| [`PIPELINE-E-SCHEDULER.md`](PIPELINE-E-SCHEDULER.md) | Quais jobs rodam em que cadência, o que cada ciclo executa, por que `rss_poller` faz mais que polling, e a armadilha do rebuild |
| [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md) | Descoberta via RSS, dedup, filtro de título, detecção de formato, janela de download por formato, filtro de frescor, disk guard, limpeza de órfãos |
| [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md) | Groq Whisper no pipeline (sem fallback) e a Transcrição Local com whisper.cpp, que é uma feature separada |
| [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md) | Seleção de cortes por IA: prompts por formato, score, limites de duração, Claude Haiku → fallback Groq LLaMA 3.3-70b |
| [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md) | FFmpeg: corte por formato, enquadramento vertical com fundo desfocado, geração e queima de legenda, marca d'água, thumbnail, e artefatos gerados |
| [`SISTEMA-PUBLICACAO.md`](SISTEMA-PUBLICACAO.md) | Quem é publicável, roteamento por nicho, round-robin, cota diária (teto rígido de 6), janela 19h–22h, OAuth por canal, TTL de clip |
| [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md) | As 10 rotas do sidecar HTTP 8090, auth fail-closed, controles de fila (pause/resume/reorder/prioritize), rejeição de clip, eventos para o Telegram |
| [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md) | Schema tabela a tabela, **suporte híbrido a MySQL e PostgreSQL**, comandos de backup (`db:backup`) e recuperação (`db:restore`) |
| [`SISTEMA-CLIP-PROCESSOR.md`](SISTEMA-CLIP-PROCESSOR.md) | Índice módulo a módulo do daemon (21 módulos), padrões comuns de código, o que o Redis guarda, tabela de env vars |
| [`ESTRATEGIA-YOUTUBE-E-BENCHMARK.md`](ESTRATEGIA-YOUTUBE-E-BENCHMARK.md) | Estratégia de conteúdo, diagnóstico do YouTube Studio (CTR/Retenção), Benchmark de concorrentes e modelo de cortes de Política (MBL/Missão) |
| [`SISTEMA-PAINEL.md`](SISTEMA-PAINEL.md) | Rotas, controllers e páginas do Laravel/Inertia; **Assistente IA (LLaMA 3.3)**, **Channel Template Studio (9:16)**, **Preview de Clipes** e **Links Úteis** |
| [`SISTEMA-ALERTAS-E-MONITORAMENTO.md`](SISTEMA-ALERTAS-E-MONITORAMENTO.md) | Observabilidade em 2 camadas: Sentry (crashes), Watchdog proativo (`watchdog.py`, auto-cura de deadlocks e clipes fantasmas) e alertas via Telegram e Email |

### Infra

| Documento | Responde |
|---|---|
| [`PLANO-ORACLE.md`](PLANO-ORACLE.md) | Migração para Oracle Cloud Always Free: decisão, como o custo zero é garantido, riscos e checklist por fase |

### Planos (nada implementado)

| Documento | Responde |
|---|---|
| [`PLANO-PROMPTS-EDITAVEIS.md`](PLANO-PROMPTS-EDITAVEIS.md) | Como tornar os prompts de seleção editáveis pelo painel, sem editar Python e sem rebuild, com métricas para comparar versões |


`.planning/` é do fluxo GSD (roadmap por fase) e **não** é fonte de verdade do estado atual.
`.planning/research/ARCHITECTURE.md` é pesquisa de junho/2026 e descreve um futuro que não aconteceu
(migração do bot para o n8n, painel em Filament) — ignorar.

---

## Estado atual em uma tela

**Stack do painel:** Laravel 13 + Inertia 3 + **React 19** + shadcn/ui + Tailwind 4 + Vite 8 +
TypeScript, desde o commit `dca6e44`. **O Filament foi removido por completo** — qualquer menção a ele
em README, nome de arquivo ou teste é resíduo, não estado atual.

**Infra:** roda 100% local em Docker, no `docker-compose.yml` da raiz `wordpress/` **compartilhado com
outros projetos** (kelnab, feeb, placebeads, riodelux, gringo). Mexer apenas no serviço
`clip-processor` e nos paths sob `canaldecortes/`. Migração para Oracle **não iniciada** — os
pré-requisitos de código (fase 1) estão em andamento.

**Problema que motivou a migração:** SSD de 228 GB chegou a 85% de uso e derrubou o Docker. Parte era
volume real, parte era vazamento de arquivo.

**Prazo externo em aberto:** a Oracle cortou o Always Free de 4 OCPU/24 GB para 2 OCPU/12 GB e desliga
instâncias fora do novo limite a partir de **18/08/2026**. Se já existe instância na conta, conferir o
shape antes dessa data — e **redimensionar, nunca terminar**.

**Bugs:** 4 corrigidos, 1 parcial, 5 abertos, 1 suspeita. Detalhe e prioridade em
[`BUGS.md`](BUGS.md).

### Corrigido em 12–13/08/2026

| O quê | Onde |
|---|---|
| `_raw.mp4` e `_subtitled.mp4` passaram a ser apagados na finalização do vídeo fonte | `publisher.py` (commit `5009112`) |
| Download falho apaga o arquivo e zera `local_path` — antes vazava disco e entupia a janela para sempre (58 vídeos, 4.1 GB, pipeline parado) | `_discard_failed_download` em `pipeline_runner.py` |
| Recovery de estado preso virou job periódico de 30 min, não só no boot | `main.py`, job `state_recovery` |
| `selecting` com `local_path IS NULL` sem update há 2 h agora vai para `failed` — antes ficava preso para sempre | terceira query de `recover_stuck_selecting` em `db.py` |
| `MIN_SHORTFORM_SECONDS` subiu de 15 s para **30 s** e o prompt do modo curto foi reescrito | `selector.py` |

### Os dois que mais doem hoje

1. **Nada em `cutting`, `publishing` ou `transcribing` tem recuperação automática** — o que travar ali
   fica preso para sempre e segura arquivo em disco (bug 4).
2. **O container não honra SIGTERM:** todo `docker stop` termina em `Exited (137)` / SIGKILL porque o
   `BlockingScheduler` não retorna do `shutdown` (bug 11). Junto com o item 1, cada restart pode criar
   um estado preso novo. Por isso o [`RUNBOOK.md`](RUNBOOK.md#reiniciar-o-clip-processor-com-segurança)
   manda conferir o que está em trânsito antes de parar o container.

---

## As três armadilhas que pegam todo mundo

1. **Editar `clip-processor/src/` não muda nada sem rebuild.** Não há bind mount; a imagem embute o
   código. Em 13/08/2026 o container rodava código de 01/08 contra um host em 12/08. **Conferir a data
   da imagem antes de investigar qualquer bug.**
   ```bash
   docker compose build clip-processor && docker compose up -d clip-processor
   ```
2. **A fila não mora no Redis.** Fila = MySQL. O Redis só tem dedup, cota e idempotência de aviso.
   Apagar as chaves `video:*` **ressuscita todo o backlog** no próximo poll. Nunca `FLUSHALL`.
3. **Ao cruzar banco × disco, filtrar pela chave, nunca pelo nome do arquivo.** `<id>.srt` e
   `<id>_raw.mp4` não estão em coluna nenhuma — comparar nomes os marca como órfãos e apaga arquivo de
   clip vivo.

Bônus: **`ANTHROPIC_API_KEY` está vazia na operação normal.** O código tenta Claude primeiro em todos os
caminhos de IA, mas quem roda de fato em produção é o **fallback Groq LLaMA 3.3-70b**. Ao ler
`selector.py` ou `metadata_generator.py`, o caminho Anthropic é o que **não** executa.

---

## Como atualizar estes documentos

Regra única: **status mora no documento, não na cabeça de ninguém.**

- Corrigiu um bug → muda o status em `BUGS.md` para FEITO, com data e commit. **Não renumerar** os
  itens; outros documentos linkam por número.
- Concluiu uma fase da migração → marca o checkbox em `PLANO-ORACLE.md`.
- Mudou comportamento de um subsistema → atualiza o `SISTEMA-*.md` dele; se mexeu em estado ou
  transição, também `ESTADOS-E-TRANSICOES.md`; se for estrutural, `ARCHITECTURE.md`.
- Descobriu incidente novo de operação destrutiva → `CLAUDE.md`, não aqui.

Ao citar código, usar sempre `arquivo:linha` clicável. Datas sempre absolutas (`13/08/2026`), nunca
relativas ("semana passada") — estes arquivos são lidos meses depois.
