# Decisões de arquitetura (ADR)

Um arquivo por decisão cara de desfazer ou de redescobrir. Mudou de ideia? Novo ADR que substitui o
antigo; o antigo ganha `Substituída por ADR-XXXX`. Nunca apagar. Modelo: [`_template.md`](_template.md)
e a skill `padroes-projeto`.

| ADR | Decisão | Status |
|---|---|---|
| [0001](0001-busca-vetorial-nas-transcricoes.md) | Busca híbrida (texto + vetor) nas transcrições, embeddings locais, degradação para texto | Aceita |
| [0002](0002-compose-isolado-por-projeto.md) | Compose isolado por projeto (proposta do Ricardo) | Rejeitada — vale o compose compartilhado e a regra de isolamento do `CLAUDE.md` |
| [0003](0003-fila-no-banco-redis-so-dedup-e-cota.md) | A fila mora no banco; Redis guarda só dedup, cota e idempotência | Aceita |
| [0004](0004-fallback-de-ia-obrigatorio.md) | Todo caminho de IA nasce com cascata Anthropic → Groq → determinístico | Aceita |
| [0005](0005-schema-do-pipeline-fora-das-migrations.md) | Schema do pipeline fora das migrations (histórico do MySQL) | Substituída pela prática atual (migrations Laravel em PostgreSQL) |
| [0006](0006-ferramentas-de-qualidade.md) | Gates de qualidade que passam no código atual, dívida em baseline | Aceita |
| [0007](0007-postgresql-17-como-banco-unico.md) | PostgreSQL 17 como banco único do painel e do clip-processor | Aceita |

Os ADRs 0002 a 0007 vieram da branch `release/rico` (Ricardo) e foram renumerados e corrigidos em
30/09/2026 para refletir a produção (PostgreSQL 17, A1). O ADR de PostgreSQL 18 nativo para o cron do
canal Hacker Libertário não foi trazido: é de outro projeto.
