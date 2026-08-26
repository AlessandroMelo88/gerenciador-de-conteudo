# ADR — registros de decisão de arquitetura

Uma decisão por arquivo, numerada, nunca editada depois de aceita (substituir por um ADR novo que
a referencia). Formato: **Contexto → Decisão → Consequências**, com status e data.

| # | Decisão | Status |
|---|---|---|
| [0001](0001-compose-isolado-por-projeto.md) | Compose isolado por projeto, sem `container_name` nem portas de banco no host | aceito · 25/08/2026 |
| [0002](0002-fila-no-mysql-redis-so-dedup-e-cota.md) | A fila mora no banco; Redis guarda só dedup, cota e idempotência | aceito · 27/07/2026 |
| [0003](0003-fallback-de-ia-obrigatorio.md) | Todo caminho de IA nasce com cascata Anthropic → Groq | aceito · 27/07/2026 |
| [0004](0004-schema-do-pipeline-fora-das-migrations.md) | Schema do pipeline em SQL bruto (`mysql/init`), fora das migrations do Laravel | aceito · 2026 (registrado 25/08/2026) |
| [0005](0005-ferramentas-de-qualidade.md) | Lint/format bloqueantes com baseline para dívida antiga; avisos e mypy informativos | aceito · 25/08/2026 |
| [0006](0006-motor-de-banco.md) | Motor de banco do pipeline (MySQL hoje; migração para PostgreSQL em andamento) | **em andamento** |

Template: [`_template.md`](_template.md).
