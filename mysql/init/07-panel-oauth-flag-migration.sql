-- Phase 8: Painel — Migration para OAuth expired flag
-- Idempotente — pode ser re-executado sem erro
-- Padrão: INFORMATION_SCHEMA + prepared statements (ver Phases 3-5, 7)
-- Executar com:
--   docker exec -i mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} clips_automation < mysql/init/07-panel-oauth-flag-migration.sql

USE clips_automation;

-- ============================================================================
-- oauth_expired_flag: sinalizado por uploader.py ao capturar RefreshError
-- Painel lê este campo para decidir se badge OAuth vira "expired" (vermelho)
-- Self-healing: uploader reseta para FALSE após upload bem-sucedido
-- ============================================================================

SET @has_col = (
  SELECT COUNT(*)
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = 'clips_automation'
    AND TABLE_NAME = 'destination_channels'
    AND COLUMN_NAME = 'oauth_expired_flag'
);
SET @sql = IF(
  @has_col = 0,
  'ALTER TABLE destination_channels ADD COLUMN oauth_expired_flag BOOLEAN NOT NULL DEFAULT FALSE AFTER active',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
