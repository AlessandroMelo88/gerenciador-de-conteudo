-- Controles de fila da janela de download (pause / prioridade / DnD).
-- Idempotente via INFORMATION_SCHEMA.
--   docker exec -i mysql mysql -u clips_user -p"${CLIPS_DB_PASSWORD}" clips_automation < mysql/init/04-queue-controls.sql

USE clips_automation;

SET @has_priority = (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation' AND TABLE_NAME = 'source_videos' AND COLUMN_NAME = 'priority'
);
SET @sql = IF(
  @has_priority = 0,
  'ALTER TABLE source_videos ADD COLUMN priority INT NOT NULL DEFAULT 0 AFTER status',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_paused = (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation' AND TABLE_NAME = 'source_videos' AND COLUMN_NAME = 'paused'
);
SET @sql = IF(
  @has_paused = 0,
  'ALTER TABLE source_videos ADD COLUMN paused TINYINT(1) NOT NULL DEFAULT 0 AFTER priority',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @has_queue_position = (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation' AND TABLE_NAME = 'source_videos' AND COLUMN_NAME = 'queue_position'
);
SET @sql = IF(
  @has_queue_position = 0,
  'ALTER TABLE source_videos ADD COLUMN queue_position INT NULL AFTER paused',
  'SELECT 1'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
