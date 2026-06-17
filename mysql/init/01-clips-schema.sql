-- Canal de Cortes — Schema clips_automation
-- Executar com: docker exec -i mysql mysql -uroot -prootpassword < mysql/init/01-clips-schema.sql
-- Idempotente: usa IF NOT EXISTS em todos os statements
--
-- ATENÇÃO: Este arquivo contém ${CLIPS_DB_PASSWORD} como placeholder.
-- Para executar, usar:
--   export $(cat .env | xargs) && envsubst < mysql/init/01-clips-schema.sql | docker exec -i mysql mysql -uroot -prootpassword
-- OU substituir manualmente antes de rodar.

CREATE DATABASE IF NOT EXISTS clips_automation
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE clips_automation;

CREATE TABLE IF NOT EXISTS source_channels (
  id INT AUTO_INCREMENT PRIMARY KEY,
  youtube_channel_id VARCHAR(64) NOT NULL UNIQUE,
  channel_name VARCHAR(255) NOT NULL,
  rss_url VARCHAR(512) NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_videos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  youtube_video_id VARCHAR(64) NOT NULL UNIQUE,
  channel_id INT NOT NULL,
  title VARCHAR(500),
  published_at TIMESTAMP,
  status ENUM(
    'pending',
    'downloading',
    'downloaded',
    'transcribing',
    'selecting',
    'cutting',
    'publishing',
    'published',
    'failed'
  ) DEFAULT 'pending',
  local_path VARCHAR(1024),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_source_videos_channel FOREIGN KEY (channel_id)
    REFERENCES source_channels(id)
);

CREATE TABLE IF NOT EXISTS generated_clips (
  id INT AUTO_INCREMENT PRIMARY KEY,
  source_video_id INT NOT NULL,
  clip_path VARCHAR(1024),
  thumbnail_path VARCHAR(1024),
  title VARCHAR(200),
  description TEXT,
  tags TEXT,
  score TINYINT,
  start_time FLOAT,
  end_time FLOAT,
  youtube_video_id VARCHAR(64),
  status ENUM('pending', 'published', 'failed') DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_generated_clips_video FOREIGN KEY (source_video_id)
    REFERENCES source_videos(id)
);

-- Usuário dedicado ao pipeline (sem acesso root)
CREATE USER IF NOT EXISTS 'clips_user'@'%' IDENTIFIED BY '${CLIPS_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON clips_automation.* TO 'clips_user'@'%';
FLUSH PRIVILEGES;
