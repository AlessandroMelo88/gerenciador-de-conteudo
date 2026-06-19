-- Phase 6 — Helper opcional para aprovar em massa o backlog de clips legados
-- em 'pending' no momento do deploy do swap publisher.py (CTRL-02).
--
-- NÃO É EXECUTADO AUTOMATICAMENTE. Use somente se o operador quiser pular
-- a fila de aprovação manual do backlog inicial.
--
-- Uso:
--   docker exec -i mysql mysql -u clips_user -p$CLIPS_DB_PASSWORD clips_automation \
--     < mysql/manual-workflow/approve-backlog.sql
--
-- Recomendação: ajustar a cláusula WHERE para limitar a clips criados ANTES
-- do timestamp de deploy do Plan 02. Substitua a data abaixo pela data real.

USE clips_automation;

UPDATE generated_clips
SET status = 'approved'
WHERE status = 'pending'
  AND created_at < '2026-06-19 00:00:00';

SELECT ROW_COUNT() AS clips_approved;
