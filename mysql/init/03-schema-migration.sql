-- Phase 3 schema migration
-- Executar com:
--   docker exec -i mysql mysql -u clips_user -p${CLIPS_DB_PASSWORD} clips_automation < mysql/init/03-schema-migration.sql
-- Idempotente via INFORMATION_SCHEMA + prepared statements.
-- MySQL 8.4 do container não aceita ADD COLUMN IF NOT EXISTS.

USE clips_automation;

-- 1. Adicionar coluna transcript_path em source_videos (Phase 3 armazena caminho do JSON)
SET @has_transcript_path = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'source_videos'
    AND COLUMN_NAME = 'transcript_path'
);
SET @sql = IF(
  @has_transcript_path = 0,
  'ALTER TABLE source_videos ADD COLUMN transcript_path VARCHAR(500) AFTER local_path',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 2. Estender ENUM de generated_clips para incluir pending_cut e cutting
ALTER TABLE generated_clips
  MODIFY COLUMN status ENUM('pending_cut', 'pending', 'cutting', 'published', 'failed') DEFAULT 'pending_cut';

-- 3. Adicionar coluna reason em generated_clips (motivo dado pelo Claude Haiku)
SET @has_reason = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'generated_clips'
    AND COLUMN_NAME = 'reason'
);
SET @sql = IF(
  @has_reason = 0,
  'ALTER TABLE generated_clips ADD COLUMN reason TEXT AFTER score',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
