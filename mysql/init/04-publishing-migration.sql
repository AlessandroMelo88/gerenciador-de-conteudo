-- Phase 5 schema migration
-- Executar com:
--   docker exec -i mysql mysql -u clips_user -p${CLIPS_DB_PASSWORD} clips_automation < mysql/init/04-publishing-migration.sql
-- Idempotente via INFORMATION_SCHEMA + prepared statements.
-- MySQL 8.4 do container não aceita ADD COLUMN IF NOT EXISTS.

USE clips_automation;

-- 1. Estender ENUM de generated_clips para incluir publishing.
ALTER TABLE generated_clips
  MODIFY COLUMN status ENUM('pending_cut', 'pending', 'cutting', 'publishing', 'published', 'failed') DEFAULT 'pending_cut';

-- 2. Adicionar published_at em generated_clips.
SET @has_published_at = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'generated_clips'
    AND COLUMN_NAME = 'published_at'
);
SET @sql = IF(
  @has_published_at = 0,
  'ALTER TABLE generated_clips ADD COLUMN published_at TIMESTAMP NULL AFTER youtube_video_id',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 3. Adicionar scheduled_for em generated_clips.
SET @has_scheduled_for = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'generated_clips'
    AND COLUMN_NAME = 'scheduled_for'
);
SET @sql = IF(
  @has_scheduled_for = 0,
  'ALTER TABLE generated_clips ADD COLUMN scheduled_for TIMESTAMP NULL AFTER published_at',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 4. Adicionar upload_error em generated_clips.
SET @has_upload_error = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'generated_clips'
    AND COLUMN_NAME = 'upload_error'
);
SET @sql = IF(
  @has_upload_error = 0,
  'ALTER TABLE generated_clips ADD COLUMN upload_error TEXT NULL AFTER scheduled_for',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
