---
phase: 07-schema-multi-canal-python-pipeline
plan: "01"
subsystem: database
tags: [mysql, migration, sql, multi-canal, idempotent]

# Dependency graph
requires:
  - phase: 05-publicacao-e-automacao-total
    provides: generated_clips table with status machine
  - phase: 06-controle-manual-n8n-telegram
    provides: source_channels with active flag, ENUM extended to approved/rejected
provides:
  - destination_channels table with slug, niche, youtube_channel_id, credit_template
  - source_channels extended with target_niche, channel_handle, blacklisted
  - generated_clips extended with destination_channel_id FK to destination_channels
  - Seed data: 2 destination channels (futebol-em-cortes, podcast-cortes)
affects:
  - 07-02 (QuotaManager por canal)
  - 07-03 (publisher multi-canal)
  - 07-04 (selector multi-canal)
  - 07-05 (rss_poller blacklist)
  - 08 (Filament resources destination_channels)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - INFORMATION_SCHEMA + prepared statements para idempotência no MySQL 8.4 (ADD COLUMN, ADD INDEX, ADD CONSTRAINT)
    - INSERT IGNORE para seed idempotente
    - UPDATE com WHERE target IS NULL para migração de dados sem sobrescrever

key-files:
  created:
    - mysql/init/06-multi-canal-migration.sql
  modified: []

key-decisions:
  - "FK destination_channel_id em generated_clips é INT NULL — clips legados permanecem válidos sem canal destino definido"
  - "youtube_channel_id usa placeholder UC_PLACEHOLDER_* — operador substitui antes de ativar canal real"
  - "blacklist UPDATE comentado no SQL — evita blacklistar canais acidentalmente em dev; operador descomenta com IDs reais"
  - "INDEX idx_blacklisted em source_channels — rss_poller filtra WHERE blacklisted = FALSE a cada poll"

patterns-established:
  - "INFORMATION_SCHEMA.STATISTICS para checar INDEX antes de ADD INDEX (complementa padrão de COLUMNS para ADD COLUMN)"
  - "Seção de seed comentado separada da DDL — operador pode executar parcialmente"

requirements-completed:
  - MCAN-01
  - MCAN-02
  - MCAN-03
  - COPY-02
  - COPY-03

# Metrics
duration: 8min
completed: 2026-06-22
---

# Phase 7 Plan 01: Schema Multi-Canal Migration Summary

**Migration SQL idempotente que cria destination_channels, estende source_channels com target_niche/channel_handle/blacklisted e adiciona FK destination_channel_id em generated_clips — base de schema para todo o pipeline multi-canal v2.0**

## Performance

- **Duration:** 8 min
- **Started:** 2026-06-22T19:41:09Z
- **Completed:** 2026-06-22T19:49:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Migration idempotente `mysql/init/06-multi-canal-migration.sql` com 151 linhas e 6 blocos INFORMATION_SCHEMA + prepared statements
- Tabela `destination_channels` com schema completo (id, slug, name, niche, youtube_channel_id, credit_template, active, timestamps)
- `source_channels` extendida com 3 colunas (target_niche, channel_handle, blacklisted) e INDEX idx_blacklisted
- `generated_clips` com coluna `destination_channel_id INT NULL` e FK nomeada `fk_generated_clips_destination_channel`
- Seed de 2 canais destino com INSERT IGNORE (futebol-em-cortes, podcast-cortes)
- UPDATE idempotente que atribui target_niche='futebol' a todos os canais ativos existentes sem target_niche

## Task Commits

Cada task foi commitada atomicamente:

1. **Task 1: Criar migration idempotente 06-multi-canal-migration.sql** - `079217f` (feat)

**Plan metadata:** (será adicionado no commit final de docs)

## Files Created/Modified

- `mysql/init/06-multi-canal-migration.sql` — Migration idempotente multi-canal: destination_channels, source_channels (+3 cols), generated_clips (+FK)

## Decisions Made

- FK `destination_channel_id` é INT NULL (não NOT NULL) para que clips legados permaneçam válidos — publisher e selector atribuem o canal ao processar
- `youtube_channel_id` usa placeholder `UC_PLACEHOLDER_*` nas seeds — evita ativar canal real por engano antes do GCP Project estar configurado
- UPDATE de blacklist fica comentado na Seção 5 — dev não blacklista acidentalmente canais reais; operador descomenta com channel_names corretos
- Bloco `INFORMATION_SCHEMA.STATISTICS` usado para verificar existência de INDEX antes de ADD INDEX (padrão complementar ao de ADD COLUMN já estabelecido)

## Deviations from Plan

None — plano executado exatamente como especificado.

## Issues Encountered

Docker daemon não respondeu durante verificação live da migration. O arquivo SQL foi validado estruturalmente (grep nos padrões obrigatórios, contagem de linhas > 80). A migration deve ser aplicada manualmente ao iniciar o container:

```bash
docker exec -i mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} clips_automation < mysql/init/06-multi-canal-migration.sql
```

## User Setup Required

Após iniciar/reiniciar o container MySQL, aplicar a migration:

```bash
# Aplicar migration
docker exec -i mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} clips_automation < mysql/init/06-multi-canal-migration.sql

# Verificar schema resultante
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "DESCRIBE destination_channels; DESCRIBE source_channels;" clips_automation

# Verificar seed
docker exec mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT id, slug, niche FROM destination_channels;" clips_automation

# Idempotência (deve retornar zero erros)
docker exec -i mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} clips_automation < mysql/init/06-multi-canal-migration.sql && echo "IDEMPOTENT OK"

# Substituir placeholders nos canais destino antes de ativar
# UPDATE destination_channels SET youtube_channel_id='UCxxx' WHERE slug='futebol-em-cortes';
# UPDATE destination_channels SET youtube_channel_id='UCyyy' WHERE slug='podcast-cortes';
```

## Next Phase Readiness

- Schema multi-canal pronto — Plans 07-02 a 07-05 podem usar destination_channels e colunas novas de source_channels
- Phase 8 (Filament) pode criar resources para destination_channels com a tabela existente
- Canais blacklistados: descomentar UPDATE na Seção 5 com channel_names reais antes de colocar em produção

---
*Phase: 07-schema-multi-canal-python-pipeline*
*Completed: 2026-06-22*
