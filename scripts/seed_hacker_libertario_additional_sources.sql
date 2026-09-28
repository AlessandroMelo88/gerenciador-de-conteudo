-- Fontes adicionais validadas para o canal de destino Hacker Libertário.
-- Execução autorizada em 2026-09-28: 3 novas fontes, total local esperado de 45.
-- Estas linhas ativam ingestão. A configuração local pode publicar automaticamente;
-- confirme direitos comerciais e o estado de aprovação do publisher antes de reaplicar
-- este seed em outro ambiente.

WITH profile AS (
    SELECT id
    FROM prompt_profiles
    WHERE slug = 'conteudo-inteligencia'
      AND niche = 'hacker-libertario'
      AND active = TRUE
), candidates (youtube_channel_id, channel_name, channel_handle, rss_url) AS (
    VALUES
        (
            'UCFfPOYpCwGt8qEd16j1Wa1Q',
            'TecSec Podcast',
            '@tecsecpodcast',
            'https://www.youtube.com/feeds/videos.xml?channel_id=UCFfPOYpCwGt8qEd16j1Wa1Q'
        ),
        (
            'UCrWvhVmt0Qac3HgsjQK62FQ',
            'Curso em Vídeo',
            '@cursoemvideo',
            'https://www.youtube.com/feeds/videos.xml?channel_id=UCrWvhVmt0Qac3HgsjQK62FQ'
        ),
        (
            'UCmiBQ-47u2O8Ia48WJ_ZDKA',
            'Flow de Dados',
            '@flowdedados',
            'https://www.youtube.com/feeds/videos.xml?channel_id=UCmiBQ-47u2O8Ia48WJ_ZDKA'
        )
)
INSERT INTO source_channels (
    youtube_channel_id,
    channel_name,
    channel_handle,
    target_niche,
    prompt_profile_id,
    rss_url,
    active,
    blacklisted
)
SELECT
    candidates.youtube_channel_id,
    candidates.channel_name,
    candidates.channel_handle,
    'hacker-libertario',
    profile.id,
    candidates.rss_url,
    TRUE,
    FALSE
FROM candidates
CROSS JOIN profile
ON CONFLICT (youtube_channel_id) DO UPDATE
SET
    channel_name = EXCLUDED.channel_name,
    channel_handle = EXCLUDED.channel_handle,
    target_niche = EXCLUDED.target_niche,
    prompt_profile_id = EXCLUDED.prompt_profile_id,
    rss_url = EXCLUDED.rss_url,
    active = EXCLUDED.active
WHERE source_channels.blacklisted = FALSE
  AND source_channels.target_niche = 'hacker-libertario';
