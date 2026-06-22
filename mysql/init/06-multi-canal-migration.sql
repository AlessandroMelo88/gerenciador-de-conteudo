-- Phase 7: Schema Multi-Canal Migration
-- Idempotente — pode ser re-executado sem erro
-- Padrão: INFORMATION_SCHEMA + prepared statements (ver fases 3-5)
-- Executar com:
--   docker exec -i mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} clips_automation < mysql/init/06-multi-canal-migration.sql

USE clips_automation;

-- =============================================================================
-- Seção 1: Criar tabela destination_channels (IF NOT EXISTS)
-- =============================================================================

CREATE TABLE IF NOT EXISTS destination_channels (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  slug               VARCHAR(50) UNIQUE NOT NULL,
  name               VARCHAR(120) NOT NULL,
  niche              VARCHAR(50) NOT NULL,
  youtube_channel_id VARCHAR(50) UNIQUE NOT NULL,
  credit_template    TEXT,
  active             BOOLEAN DEFAULT TRUE,
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- =============================================================================
-- Seção 2: ALTER source_channels — 3 novas colunas (idempotente via INFORMATION_SCHEMA)
-- =============================================================================

-- 2.1 target_niche: qual nicho esse canal-fonte alimenta
SET @has_col = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'source_channels'
    AND COLUMN_NAME = 'target_niche'
);
SET @sql = IF(
  @has_col = 0,
  'ALTER TABLE source_channels ADD COLUMN target_niche VARCHAR(50) NULL AFTER channel_name',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.2 channel_handle: ex: @sportv para créditos na descrição
SET @has_col = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'source_channels'
    AND COLUMN_NAME = 'channel_handle'
);
SET @sql = IF(
  @has_col = 0,
  'ALTER TABLE source_channels ADD COLUMN channel_handle VARCHAR(100) NULL AFTER target_niche',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.3 blacklisted: bloqueia download no rss_poller
SET @has_col = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'source_channels'
    AND COLUMN_NAME = 'blacklisted'
);
SET @sql = IF(
  @has_col = 0,
  'ALTER TABLE source_channels ADD COLUMN blacklisted BOOLEAN NOT NULL DEFAULT FALSE AFTER channel_handle',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2.4 INDEX em blacklisted (rss_poller filtra WHERE blacklisted = FALSE)
SET @has_idx = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'source_channels'
    AND INDEX_NAME = 'idx_blacklisted'
);
SET @sql = IF(
  @has_idx = 0,
  'ALTER TABLE source_channels ADD INDEX idx_blacklisted (blacklisted)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =============================================================================
-- Seção 3: ALTER generated_clips — destination_channel_id com FK
-- =============================================================================

-- 3.1 Adicionar coluna destination_channel_id
SET @has_col = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'generated_clips'
    AND COLUMN_NAME = 'destination_channel_id'
);
SET @sql = IF(
  @has_col = 0,
  'ALTER TABLE generated_clips ADD COLUMN destination_channel_id INT NULL AFTER source_video_id',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3.2 Adicionar FK destination_channel_id -> destination_channels(id)
SET @has_fk = (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'generated_clips'
    AND CONSTRAINT_NAME = 'fk_generated_clips_destination_channel'
);
SET @sql = IF(
  @has_fk = 0,
  'ALTER TABLE generated_clips ADD CONSTRAINT fk_generated_clips_destination_channel FOREIGN KEY (destination_channel_id) REFERENCES destination_channels(id)',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- =============================================================================
-- Seção 4: Seed destination_channels (INSERT IGNORE para idempotência)
-- =============================================================================

INSERT IGNORE INTO destination_channels (slug, name, niche, youtube_channel_id, credit_template, active)
VALUES
  ('futebol-em-cortes', 'Futebol em Cortes', 'futebol', 'UC_PLACEHOLDER_FUTEBOL', 'Créditos: @{channel_handle}', TRUE),
  ('podcast-cortes',    'Podcast Cortes',     'podcast', 'UC_PLACEHOLDER_PODCAST',  'Créditos: @{channel_handle}', TRUE);

-- =============================================================================
-- Seção 5: UPDATE source_channels com target_niche padrão e blacklist inicial
-- =============================================================================

-- Todos os canais ativos existentes recebem target_niche='futebol' como padrão se ainda NULL
UPDATE source_channels SET target_niche = 'futebol' WHERE target_niche IS NULL AND active = TRUE;

-- Canais blacklistados (IDs placeholder — operador preenche com IDs reais)
-- UPDATE source_channels SET blacklisted = TRUE WHERE channel_name IN ('Globo Esporte','SBT','Band');
