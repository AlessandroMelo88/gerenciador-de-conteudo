-- Phase 6 — adiciona approved/rejected ao ENUM. publisher.py passa a publicar approved (Plan 02).
-- Executar com:
--   docker exec -i mysql mysql -u clips_user -p${CLIPS_DB_PASSWORD} clips_automation < mysql/init/05-controle-manual-migration.sql
-- Idempotente: ALTER TABLE ... MODIFY COLUMN com ENUM completo é no-op se o ENUM já estiver no estado final.
-- MySQL 8.4: adicionar valores ao final do ENUM é operação metadata-only (não reescreve a tabela).

USE clips_automation;

-- Estender ENUM de generated_clips para incluir approved (substitui pending na fila de publicação)
-- e rejected (operador descartou via Telegram). Default permanece pending_cut.
ALTER TABLE generated_clips
  MODIFY COLUMN status ENUM(
    'pending_cut',
    'pending',
    'cutting',
    'publishing',
    'published',
    'failed',
    'approved',
    'rejected'
  ) DEFAULT 'pending_cut';
