-- Canal de Cortes — Seed de canais-fonte para monitoramento
-- Phase 2: Aquisição de Vídeos
-- Idempotente: INSERT IGNORE para re-execução segura
-- Executar: docker exec -i mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} clips_automation < mysql/init/02-seed-channels.sql

USE clips_automation;

INSERT IGNORE INTO source_channels (youtube_channel_id, channel_name, rss_url, active)
VALUES
  -- SporTV: canal oficial do SporTV no YouTube (coberturas ao vivo de futebol)
  ('UC_s__6CQ2hcRzDSGpMlIbDg', 'SporTV',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UC_s__6CQ2hcRzDSGpMlIbDg', TRUE),

  -- ge.globo: canal do Globoesporte, maior cobertura de futebol do Brasil
  ('UCcxEFCDEUwXrMI6d_Wn3c6Q', 'ge.globo',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCcxEFCDEUwXrMI6d_Wn3c6Q', TRUE),

  -- ESPN Brasil: análises, mesas redondas e melhores momentos
  ('UCGgLrGi5EIhIlyNJGdHKzog', 'ESPN Brasil',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCGgLrGi5EIhIlyNJGdHKzog', TRUE),

  -- Canal do Nicola (Jorge Nicola): mercado de transferências, bastidores
  ('UCqfQER98ceoJy1J-X5TZMlQ', 'Canal do Nicola',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCqfQER98ceoJy1J-X5TZMlQ', TRUE),

  -- TNT Sports Brasil: Champions League, torneios internacionais
  ('UCOxuBMv4QH0XOxbwi35ZVJQ', 'TNT Sports Brasil',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCOxuBMv4QH0XOxbwi35ZVJQ', TRUE);
