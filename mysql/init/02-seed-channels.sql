-- Canal de Cortes — Seed de canais-fonte para monitoramento
-- Phase 2: Aquisição de Vídeos
-- Idempotente: INSERT IGNORE para re-execução segura
-- Executar: docker exec -i mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} clips_automation < mysql/init/02-seed-channels.sql
-- IDs verificados em 2026-06-19

USE clips_automation;

INSERT IGNORE INTO source_channels (youtube_channel_id, channel_name, rss_url, active)
VALUES
  -- SporTV: @canalSporTV — coberturas ao vivo de futebol
  ('UCrD2l7nEg6AATX5qfugm8Xg', 'SporTV',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCrD2l7nEg6AATX5qfugm8Xg', TRUE),

  -- GloboEsporte: @GloboEsporte — maior cobertura de futebol do Brasil
  ('UCS710QGV74b0wPETkrcVB7w', 'ge.globo',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCS710QGV74b0wPETkrcVB7w', TRUE),

  -- ESPN Brasil: @espnbrasil — análises, mesas redondas e melhores momentos
  ('UCw5-xj3AKqEizC7MvHaIPqA', 'ESPN Brasil',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCw5-xj3AKqEizC7MvHaIPqA', TRUE),

  -- Canal do Nicola: @CanalDoNicola — mercado de transferências, bastidores
  ('UCx0RRbF4EJOUQ28SurIU7Eg', 'Canal do Nicola',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCx0RRbF4EJOUQ28SurIU7Eg', TRUE),

  -- TNT Sports Brasil: @TNTSportsBR — Champions League, torneios internacionais
  ('UCs-6sCz2LJm1PrWQN4ErsPw', 'TNT Sports Brasil',
   'https://www.youtube.com/feeds/videos.xml?channel_id=UCs-6sCz2LJm1PrWQN4ErsPw', TRUE);
