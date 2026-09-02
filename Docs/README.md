# Documentação — Canal de Cortes

> **Tipo:** índice · **Status:** atualizado · **Data:** 2026-08-27

Use esta página para escolher a referência certa. Documentos marcados como `as-built` descrevem o
código atual; planos, ADRs, bugs e changelog registram decisões ou histórico.

## Leitura recomendada

| Objetivo | Documento |
|---|---|
| Entender o sistema | [`../README.md`](../README.md) e [`../ARCHITECTURE.md`](../ARCHITECTURE.md) |
| Operar ou diagnosticar | [`RUNBOOK.md`](RUNBOOK.md) e [`../CLAUDE.md`](../CLAUDE.md) |
| Entender a fila | [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md) |
| Entender IA, perfis e prompts | [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md) |
| Alterar código | [`DESENVOLVIMENTO.md`](DESENVOLVIMENTO.md) e [`../CONTRIBUTING.md`](../CONTRIBUTING.md) |

## Referências as-built

| Documento | Escopo | Fonte de verdade |
|---|---|---|
| [`PIPELINE-E-SCHEDULER.md`](PIPELINE-E-SCHEDULER.md) | workers por etapa, filas e recovery | `src/worker.py`, `docker-compose.yml` |
| [`SISTEMA-DOWNLOAD.md`](SISTEMA-DOWNLOAD.md) | RSS, dedup, download e janela | `rss_poller.py`, `dedup.py`, `downloader.py` |
| [`SISTEMA-TRANSCRICAO.md`](SISTEMA-TRANSCRICAO.md) | legendas, Groq Whisper e transcrição local | `transcriber.py`, `transcription_job.py` |
| [`SISTEMA-IA-SELECAO.md`](SISTEMA-IA-SELECAO.md) | prompts, providers e validação | `selector.py`, `metadata_generator.py` |
| [`SISTEMA-VIDEO.md`](SISTEMA-VIDEO.md) | FFmpeg, assets e artefatos | `video_processor.py`, `media_*.py` |
| [`SISTEMA-PUBLICACAO.md`](SISTEMA-PUBLICACAO.md) | quota, OAuth e upload | `publisher.py`, `quota_manager.py`, `uploader.py` |
| [`SISTEMA-SIDECAR.md`](SISTEMA-SIDECAR.md) | API interna e controles | `internal_api.py`, `queue_controls.py` |
| [`SISTEMA-CLIP-PROCESSOR.md`](SISTEMA-CLIP-PROCESSOR.md) | mapa dos módulos Python | `clip-processor/src/` |
| [`SISTEMA-PAINEL.md`](SISTEMA-PAINEL.md) | rotas, páginas e controllers | `painel/routes/`, `painel/app/` |
| [`BANCO-DE-DADOS.md`](BANCO-DE-DADOS.md) | schema e donos das escritas | `painel/database/migrations/` |
| [`ESTADOS-E-TRANSICOES.md`](ESTADOS-E-TRANSICOES.md) | estados, transições e recovery | migrations + código Python/PHP |

## Operação e desenvolvimento

| Documento | Uso |
|---|---|
| [`RUNBOOK.md`](RUNBOOK.md) | saúde, logs, reinício, fila, disco e backup |
| [`DESENVOLVIMENTO.md`](DESENVOLVIMENTO.md) | setup, lint, testes, CI e release |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | branches, commits e changelog |
| [`../CLAUDE.md`](../CLAUDE.md) | regras de segurança para operações destrutivas |
| [`ADR/README.md`](ADR/README.md) | decisões de arquitetura aceitas ou substituídas |

## Histórico e planejamento

Estes arquivos não devem ser usados para inferir o comportamento atual sem conferir o código:

| Documento | Natureza |
|---|---|
| [`BUGS.md`](BUGS.md) | backlog e incidentes; itens podem estar desatualizados |
| [`TODO-REFATORACAO.md`](TODO-REFATORACAO.md) | auditoria técnica datada |
| [`PLANO-ORACLE.md`](PLANO-ORACLE.md) | migração futura; não iniciada |
| [`PLANO-PROMPTS-EDITAVEIS.md`](PLANO-PROMPTS-EDITAVEIS.md) | editor/versionamento futuro; perfis-base já implementados |
| [`../CHANGELOG.md`](../CHANGELOG.md) e [`../CHANGELOG.d/`](../CHANGELOG.d/README.md) | histórico de mudanças |
| [`ADR/`](ADR/README.md) | decisões preservadas, inclusive as substituídas |

`.planning/` contém planejamento GSD. `graphify-out/` contém o grafo do projeto. Nenhum dos dois
substitui o código executado.

## Regras de manutenção

- comportamento alterado → atualize o documento do subsistema;
- mudança de estado → atualize `ESTADOS-E-TRANSICOES.md`;
- decisão estrutural → crie um ADR novo, sem editar um ADR aceito;
- mudança relevante → adicione fragmento em `CHANGELOG.d/`;
- use datas absolutas no formato `YYYY-MM-DD`;
- em conflito, prefira código, migrations, Compose e `.env.example`, nessa ordem.
