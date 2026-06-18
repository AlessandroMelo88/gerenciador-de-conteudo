-- Phase 3 schema migration
-- Executar com:
--   docker exec -i mysql mysql -u clips_user -p${CLIPS_DB_PASSWORD} clips_automation < mysql/init/03-schema-migration.sql
-- Idempotente via IF NOT EXISTS / MODIFY com valores já existentes (MySQL aceita MODIFY mesmo que a coluna já tenha o valor)

USE clips_automation;

-- 1. Adicionar coluna transcript_path em source_videos (Phase 3 armazena caminho do JSON)
ALTER TABLE source_videos
  ADD COLUMN IF NOT EXISTS transcript_path VARCHAR(500) AFTER local_path;

-- 2. Estender ENUM de generated_clips para incluir pending_cut e cutting
ALTER TABLE generated_clips
  MODIFY COLUMN status ENUM('pending_cut', 'pending', 'cutting', 'published', 'failed') DEFAULT 'pending_cut';

-- 3. Adicionar coluna reason em generated_clips (motivo dado pelo Claude Haiku)
ALTER TABLE generated_clips
  ADD COLUMN IF NOT EXISTS reason TEXT AFTER score;
