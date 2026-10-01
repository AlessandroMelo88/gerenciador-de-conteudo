# Docs/sistema — como o sistema funciona

**O que mora aqui:** a referência *as-built* de cada subsistema, escrita a partir do código. Nada de
plano nem de histórico: o que ainda vai ser feito está em [`../planos/`](../planos/), os comandos do dia
a dia em [`../operacao/`](../operacao/), o que ficou para trás em [`../historico/`](../historico/).
Visão geral de tudo: [`../README.md`](../README.md). O que está feito e o que falta: [`../PROGRESSO.md`](../PROGRESSO.md).

Estado de todos os documentos desta pasta: **VIGENTE** (exceto onde indicado).

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

## Documentos desta pasta

### Pipeline (o robô)

| Documento | Responde |
|---|---|
| [`SISTEMA-CLIP-PROCESSOR.md`](SISTEMA-CLIP-PROCESSOR.md) | Índice módulo a módulo do daemon (21 módulos), padrões comuns de código, o que o Redis guarda, tabela de env vars. **Comece por aqui** |
| [`PIPELINE-E-SCHEDULER.md`](PIPELINE-E-SCHEDULER.md) | Quais jobs rodam em que cadência, o que cada ciclo executa, por que `rss_poller` faz mais que polling, e a armadilha do rebuild |
| [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md) | Máquina de estados de `source_videos` e `generated_clips`, quem escreve cada transição, **o que tem e o que não tem recuperação automática**, e o que ocupa vaga na janela de download |
| [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md) | Descoberta via RSS, dedup, filtro de título, detecção de formato, janela de download por formato, filtro de frescor, disk guard, limpeza de órfãos |
| [`SISTEMA-FRESCOR-E-PRIORIDADE.md`](SISTEMA-FRESCOR-E-PRIORIDADE.md) | Janela de busca e prioridade de input por canal-fonte (tela Canais Fonte) |
| [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md) | Groq Whisper no pipeline (sem fallback) e a base de conhecimento de transcrições (worker do Mac, extensão do Chrome, aulas HLS), feature separada |
| [`SISTEMA-BUSCA-TRANSCRICOES.md`](SISTEMA-BUSCA-TRANSCRICOES.md) | Busca das transcrições: texto × semântica × híbrida (com exemplos para o usuário), `transcript_chunks`, pgvector/HNSW, RRF, sidecar `embedder`, backfill, runbook de rollout e reindex |
| [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md) | Seleção de cortes por IA: prompts por formato, score, limites de duração, Claude Haiku → fallback Groq LLaMA 3.3-70b |
| [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md) | FFmpeg: corte por formato, enquadramento vertical com fundo desfocado, legenda, marca d'água, thumbnail, artefatos gerados |
| [`SISTEMA-MIDIA-POR-CANAL.md`](SISTEMA-MIDIA-POR-CANAL.md) | Intro, encerramento e música de fundo por canal destino |
| [`SISTEMA-PUBLICACAO.md`](SISTEMA-PUBLICACAO.md) | Quem é publicável, roteamento por nicho, round-robin, cota diária (teto rígido de 6), janela 19h–22h, OAuth por canal, TTL de clip |
| [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md) | As rotas do sidecar HTTP 8090, auth fail-closed, controles de fila, rejeição de clip, eventos para o Telegram |
| [`SISTEMA-REGRAS-E-GATILHOS.md`](SISTEMA-REGRAS-E-GATILHOS.md) | **VERIFICAR.** Resumo antigo de metas e janelas; contradiz os dois documentos acima (publicação e download) |

### Painel, dados, observabilidade e negócio

| Documento | Responde |
|---|---|
| [`SISTEMA-PAINEL.md`](SISTEMA-PAINEL.md) | Rotas, controllers e páginas do Laravel/Inertia; Assistente IA, Channel Template Studio (9:16), Preview de Clipes, Links Úteis |
| [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md) | Schema tabela a tabela, suporte híbrido MySQL/PostgreSQL, backup (`db:backup`) e recuperação (`db:restore`) |
| [`SISTEMA-ALERTAS-E-MONITORAMENTO.md`](SISTEMA-ALERTAS-E-MONITORAMENTO.md) | Better Stack, Sentry, Watchdog proativo (auto-cura de deadlocks e clipes fantasmas), alertas via Telegram e e-mail |
| [`SISTEMA-AFILIADOS.md`](SISTEMA-AFILIADOS.md) | Ofertas de afiliado: `affiliate-worker` local, `POST /api/offers` com token fail-closed, tela Ofertas, redirect rastreável `/o/{slug}`, Telegram, tema Umbrella |

Fora desta pasta, mas parte do "como funciona": [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md)
(arquitetura as-built, primeira leitura de quem chega) e [`../adr/`](../adr/README.md) (por que foi decidido assim).

`.planning/` é do fluxo GSD (roadmap por fase) e **não** é fonte de verdade do estado atual.
`.planning/research/ARCHITECTURE.md` é pesquisa de junho/2026 e descreve um futuro que não aconteceu
(migração do bot para o n8n, painel em Filament) — ignorar.

---

## As três armadilhas que pegam todo mundo

1. **Editar `clip-processor/src/` não muda nada sem rebuild.** Não há bind mount; a imagem embute o
   código. Em 13/08/2026 o container rodava código de 01/08 contra um host em 12/08. **Conferir a data
   da imagem antes de investigar qualquer bug.**
   ```bash
   docker compose build clip-processor && docker compose up -d clip-processor
   ```
2. **A fila não mora no Redis.** Fila = banco (PostgreSQL desde 17/09/2026). O Redis só tem dedup, cota e idempotência de aviso.
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

- Corrigiu um bug → muda o status em [`../operacao/BUGS.md`](../operacao/BUGS.md) para FEITO, com data e commit. **Não renumerar** os
  itens; outros documentos linkam por número.
- Concluiu uma etapa de plano → marca o checkbox no `PLANO-*` (em [`../planos/`](../planos/)) e atualiza a linha em [`../PROGRESSO.md`](../PROGRESSO.md).
- Mudou comportamento de um subsistema → atualiza o `SISTEMA-*.md` dele; se mexeu em estado ou
  transição, também `ESTADOS-E-TRANSICOES.md`; se for estrutural, `ARCHITECTURE.md`.
- Descobriu incidente novo de operação destrutiva → `CLAUDE.md`, não aqui.
- Moveu ou renomeou um documento → rode `python3 scripts/check-doc-links.py` (tem que dar 0 quebrados).

Ao citar código, usar sempre `arquivo:linha` clicável. Datas sempre absolutas (`13/08/2026`), nunca
relativas ("semana passada") — estes arquivos são lidos meses depois.
