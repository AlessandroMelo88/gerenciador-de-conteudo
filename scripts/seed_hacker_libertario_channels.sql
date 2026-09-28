-- seed_hacker_libertario_channels.sql
-- Inserção idempotente dos melhores canais de tecnologia, hacking, Linux, soberania digital e podcasts
-- para a esteira de Shorts do canal Hacker Libertário (target_niche = 'hacker-libertario', prompt_profile_id = 2)

INSERT INTO source_channels (youtube_channel_id, channel_name, channel_handle, target_niche, prompt_profile_id, rss_url, active, blacklisted)
VALUES
    -- 1. Hacking, Cibersegurança & Engenharia Reversa
    ('UC70YG2WHVxlOJRng4v-CIFQ', 'Gabriel Pato', '@GabrielPato', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UC70YG2WHVxlOJRng4v-CIFQ', true, false),
    ('UCFDMjyZ-fgXM4kEy-ZRCtaQ', 'CROWSEC', '@crowsec', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCFDMjyZ-fgXM4kEy-ZRCtaQ', true, false),
    ('UCkfyKm2S5eSurJDt3TATq-A', 'Guia Anônima', '@guianonima', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCkfyKm2S5eSurJDt3TATq-A', true, false),
    ('UCuQ8zW9VmVyml7KytSqJDzg', 'Mente Binária', '@mentebinaria', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCuQ8zW9VmVyml7KytSqJDzg', true, false),
    ('UC_d04_YVBL6kDiztglP82gw', 'Solyd Offensive Security', '@solyd', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UC_d04_YVBL6kDiztglP82gw', true, false),
    ('UCbTtcwb7NgrZNKN2g84fOIQ', 'Bruno Fraga', '@brunofragax', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbTtcwb7NgrZNKN2g84fOIQ', true, false),
    ('UCvSlG4nhD_vo0NsYkXcuL5w', 'Guia do Hacker', '@guiadohacker', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCvSlG4nhD_vo0NsYkXcuL5w', true, false),
    ('UCXXRHvB1akx7rptJyT2zm2Q', 'Hacking na Web', '@HackingnaWeb', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCXXRHvB1akx7rptJyT2zm2Q', true, false),

    -- 2. Cypherpunk, Soberania Digital & Liberdade
    ('UCSyG9ph5BJSmPRyzc_eGC4g', 'Visão Libertária', '@Visao_Libertaria', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCSyG9ph5BJSmPRyzc_eGC4g', true, false),
    ('UCLTWPE7XrHEe8m_xAmNbQ-Q', 'ANCAPSU', '@ancap_su', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCLTWPE7XrHEe8m_xAmNbQ-Q', true, false),
    ('UCLJkh3QjHsLtK0LZFd28oGg', 'Fernando Ulrich', '@FernandoUlrichCanal', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCLJkh3QjHsLtK0LZFd28oGg', true, false),
    ('UCC-r6vnXtcwBYq0VxZYhoXg', 'Renato Amoedo (Rotina do Trezoitão)', '@rotinadotrezoitao', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCC-r6vnXtcwBYq0VxZYhoXg', true, false),
    ('UCtevddatnL9TuZkRgaQKqJQ', 'Cortes Renato Trezoitão', '@TrezoitãoBrocador', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCtevddatnL9TuZkRgaQKqJQ', true, false),

    -- 3. Linux, Open Source & Sysadmin
    ('UCEf5U1dB5a2e2S-XUlnhxSA', 'Diolinux', '@Diolinux', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCEf5U1dB5a2e2S-XUlnhxSA', true, false),
    ('UCKlJsjG41vOzwVdXE85SdIg', 'DioCast', '@diocast', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCKlJsjG41vOzwVdXE85SdIg', true, false),
    ('UC629vKGFPRc1rz6VDm6OZiQ', 'Diolinux Labs', '@Diolinuxlabs', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UC629vKGFPRc1rz6VDm6OZiQ', true, false),
    ('UClz3DneoYlccluy4hBlx86Q', 'Slackjeff', '@Slackjeff', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UClz3DneoYlccluy4hBlx86Q', true, false),
    ('UC8EGrwe_DXSzrCQclf_pv9g', 'debxp (Blau Araujo)', '@debxp', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UC8EGrwe_DXSzrCQclf_pv9g', true, false),
    ('UCJnKVGmXRXrH49Tvrx5X0Sw', 'LINUXtips', '@LINUXtips', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCJnKVGmXRXrH49Tvrx5X0Sw', true, false),
    ('UCzOGJclZQvPVgYZIwERsf5g', 'Bóson Treinamentos', '@bosontreinamentos', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCzOGJclZQvPVgYZIwERsf5g', true, false),

    -- 4. Programação, Cultura Dev & Tech News
    ('UCU5JicSrEM5A63jkJ2QvGYw', 'Filipe Deschamps', '@filipedeschamps', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCU5JicSrEM5A63jkJ2QvGYw', true, false),
    ('UCzR2u5RWXWjUh7CwLSvbitA', 'Mario Souto (Dev Soutinho)', '@DevSoutinho', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCzR2u5RWXWjUh7CwLSvbitA', true, false),
    ('UCkqOofjb7nl6V8vXrIbGtiQ', 'Rodrigo Branas', '@RodrigoBranas', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCkqOofjb7nl6V8vXrIbGtiQ', true, false),
    ('UCBYJKJXaigXVTVsr2UmtWyg', 'Programador Lhama', '@ProgramadorLhama', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCBYJKJXaigXVTVsr2UmtWyg', true, false),
    ('UCetRsdZxDQDcgVDJd6erz6g', 'Attekita Dev', '@attekitadev', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCetRsdZxDQDcgVDJd6erz6g', true, false),
    ('UCpKvMmsF6QrkVr_zWaLGK-A', 'Fernanda Kipper', '@kipperdev', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCpKvMmsF6QrkVr_zWaLGK-A', true, false),
    ('UCSfwM5u0Kce6Cce8_S72olg', 'Rocketseat', '@rocketseat', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCSfwM5u0Kce6Cce8_S72olg', true, false),

    -- 5. Inteligência Artificial & Dados
    ('UCEn6kONg6EC_Ylh0RlInsMw', 'Universo Discreto', '@UniversoDiscreto', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCEn6kONg6EC_Ylh0RlInsMw', true, false),
    ('UCIQne9yW4TvCCNYQLszfXCQ', 'Sandeco', '@canalsandeco', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCIQne9yW4TvCCNYQLszfXCQ', true, false),
    ('UCxXL5491Db9U8Rhfs-2LVFg', 'Asimov Academy', '@AsimovAcademy', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCxXL5491Db9U8Rhfs-2LVFg', true, false),
    ('UC-Xa9J9-B4jBOoBNIHkMMKA', 'Téo Me Why', '@teomewhy', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UC-Xa9J9-B4jBOoBNIHkMMKA', true, false),

    -- 6. Canais de Cortes & Podcasts Especializados
    ('UCbiNMBd57pgETEFbiDSa4yQ', 'Cortes do Ciência Sem Fim', '@CortesCienciaSemFim', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbiNMBd57pgETEFbiDSa4yQ', true, false),
    ('UC3uYvpJ3J6oNoNYRXfZXjEw', 'Cortes do Flow', '@cortesdoflow', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UC3uYvpJ3J6oNoNYRXfZXjEw', true, false),
    ('UCvmWNQH4c2T3Triih3lftiw', 'Cortes do Inteligência', '@cortesdointeligencia', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCvmWNQH4c2T3Triih3lftiw', true, false),
    ('UCI_kaJaYXESDVmO3ZhUEYIQ', 'Segurança Legal', '@SegurançaLegal', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCI_kaJaYXESDVmO3ZhUEYIQ', true, false),
    ('UCqXz9JHRFGDZA6zyCeO29Rw', 'Papo de Dev', '@canalpapodedev', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCqXz9JHRFGDZA6zyCeO29Rw', true, false),
    ('UCzJPdSTGj7KPZLjaOatWS4A', 'Os Sócios Podcast', '@ossocios', 'hacker-libertario', 2, 'https://www.youtube.com/feeds/videos.xml?channel_id=UCzJPdSTGj7KPZLjaOatWS4A', true, false)
ON CONFLICT (youtube_channel_id) DO UPDATE
SET channel_name = EXCLUDED.channel_name,
    channel_handle = EXCLUDED.channel_handle,
    target_niche = EXCLUDED.target_niche,
    prompt_profile_id = EXCLUDED.prompt_profile_id,
    rss_url = EXCLUDED.rss_url,
    active = true;
