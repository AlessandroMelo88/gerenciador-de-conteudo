+# ADRs — decisões de arquitetura

> **Tipo:** registro histórico de decisões. ADRs aceitos não são a fonte do comportamento atual;
> quando uma decisão é substituída, o documento as-built e o código prevalecem.

Cada decisão fica em um arquivo numerado, no formato **Contexto → Decisão → Consequências**.
Decisões novas devem criar outro ADR; não reescreva o histórico para refletir o runtime atual.

| ADR | Tema | Estado em 2026-08-26 |
|---|---|---|
| [0001](0001-compose-isolado-por-projeto.md) | Compose isolado por projeto | histórico; a topologia atual está em [../../ARCHITECTURE.md](../../ARCHITECTURE.md) |
| [0002](0002-fila-no-mysql-redis-so-dedup-e-cota.md) | fila no banco; Redis para dedup, cota e idempotência | decisão conceitual vigente; o banco atual é PostgreSQL |
| [0003](0003-fallback-de-ia-obrigatorio.md) | cascata de providers de IA | substituído; seleção, metadata e thumbnail têm regras próprias em [../SISTEMA-IA-SELECAO.md](../SISTEMA-IA-SELECAO.md) |
| [0004](0004-schema-do-pipeline-fora-das-migrations.md) | schema fora das migrations Laravel | substituído pelo PostgreSQL e pelas migrations atuais |
| [0005](0005-ferramentas-de-qualidade.md) | lint, formatação, tipos e CI | histórico; o contrato atual está em [../DESENVOLVIMENTO.md](../DESENVOLVIMENTO.md) |
| [0006](0006-motor-de-banco.md) | PostgreSQL 16 como banco único | vigente |

Os números 0007 e 0008 não existem neste repositório e não devem ser referenciados como
decisões válidas. A gestão atual do schema e os gates de qualidade estão nos documentos as-built.

Modelo: [_template.md](_template.md).
