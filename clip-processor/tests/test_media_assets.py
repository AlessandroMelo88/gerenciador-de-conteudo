from unittest.mock import MagicMock

import src.media_assets as media_assets
from src.media_assets import (
    choose_media_asset,
    resolve_filesystem_media_assets,
    resolve_media_assets,
)


def test_choose_media_asset_prefers_channel_and_format_scope():
    candidates = [
        {'id': 1, 'destination_channel_id': None, 'format': None, 'priority': 100},
        {'id': 2, 'destination_channel_id': 7, 'format': None, 'priority': 1},
        {'id': 3, 'destination_channel_id': None, 'format': 'curto', 'priority': 1},
        {'id': 4, 'destination_channel_id': 7, 'format': 'curto', 'priority': 1},
    ]

    result = choose_media_asset(
        candidates,
        destination_channel_id=7,
        video_format='curto',
        clip_id=0,
    )

    assert result == candidates[3]


def test_choose_media_asset_uses_priority_before_rotation():
    candidates = [
        {'id': 10, 'destination_channel_id': 7, 'format': None, 'priority': 1},
        {'id': 11, 'destination_channel_id': 7, 'format': None, 'priority': 5},
    ]

    result = choose_media_asset(
        candidates,
        destination_channel_id=7,
        video_format='longo',
        clip_id=99,
    )

    assert result == candidates[1]


def test_choose_media_asset_rotates_equivalent_assets_by_clip_id():
    candidates = [
        {'id': 20, 'destination_channel_id': 7, 'format': None, 'priority': 0},
        {'id': 21, 'destination_channel_id': 7, 'format': None, 'priority': 0},
    ]

    result = choose_media_asset(
        candidates,
        destination_channel_id=7,
        video_format='curto',
        clip_id=1,
    )

    assert result == candidates[1]


def test_resolve_media_assets_rolls_back_optional_table_failure(tmp_path, monkeypatch):
    """A ausência da tabela opcional não pode abortar a transação do clip."""
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', tmp_path / 'empty-channels')
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = False
    cursor.execute.side_effect = RuntimeError('media_assets does not exist')
    conn.cursor.return_value = cursor

    result = resolve_media_assets(
        conn,
        destination_channel_id=7,
        video_format='longo',
        clip_id=84,
    )

    assert result == {}
    assert conn.rollback.call_count == 3


def test_resolve_media_assets_skips_all_assets_for_shorts():
    conn = MagicMock()

    result = resolve_media_assets(
        conn,
        destination_channel_id=None,
        video_format='curto',
        clip_id=84,
    )

    assert result == {}
    conn.cursor.assert_not_called()


def test_resolve_filesystem_assets_prefers_video_and_rotates_audio(tmp_path, monkeypatch):
    channels_root = tmp_path / 'channels'
    channel_root = channels_root / 'hacker-libertario'
    channel_root.mkdir(parents=True)
    channel_audio = channel_root / 'audio'
    channel_audio.mkdir()

    for filename in ('intro.mp4', 'intro.jpg', 'encerramento.mp4', 'encerramento.jpg'):
        (channel_root / filename).write_bytes(b'asset')
    (channel_audio / 'a.wav').write_bytes(b'audio')

    monkeypatch.setattr(media_assets, 'ASSETS_ROOT', tmp_path)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', channels_root)

    result = resolve_filesystem_media_assets(
        channel_slug='hacker-libertario',
        video_format='longo',
        clip_id=0,
    )

    assert result['intro']['absolute_path'] == str(channel_root / 'intro.mp4')
    assert result['outro']['absolute_path'] == str(channel_root / 'encerramento.mp4')
    assert result['music']['absolute_path'] == str(channel_audio / 'a.wav')


def test_resolve_filesystem_assets_uses_images_when_video_is_missing(tmp_path, monkeypatch):
    channels_root = tmp_path / 'channels'
    channel_root = channels_root / 'canal'
    channel_root.mkdir(parents=True)
    (channel_root / 'intro.jpg').write_bytes(b'intro')
    (channel_root / 'encerramento.jpg').write_bytes(b'outro')

    monkeypatch.setattr(media_assets, 'ASSETS_ROOT', tmp_path)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', channels_root)

    result = resolve_filesystem_media_assets(
        channel_slug='canal',
        video_format='longo',
        clip_id=0,
    )

    assert result['intro']['absolute_path'] == str(channel_root / 'intro.jpg')
    assert result['outro']['absolute_path'] == str(channel_root / 'encerramento.jpg')
    assert 'music' not in result


def test_resolve_filesystem_assets_skips_identity_for_shorts(tmp_path, monkeypatch):
    channels_root = tmp_path / 'channels'
    channel_root = channels_root / 'canal'
    channel_root.mkdir(parents=True)
    (channel_root / 'intro.mp4').write_bytes(b'intro')
    (channel_root / 'encerramento.mp4').write_bytes(b'outro')

    monkeypatch.setattr(media_assets, 'ASSETS_ROOT', tmp_path)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', channels_root)

    result = resolve_filesystem_media_assets(
        channel_slug='canal',
        video_format='curto',
        clip_id=0,
    )

    assert result == {}


def test_resolve_filesystem_assets_prefers_channel_specific_audio(tmp_path, monkeypatch):
    channels_root = tmp_path / 'channels'
    channel_root = channels_root / 'canal'
    channel_audio = channel_root / 'audio'
    channel_audio.mkdir(parents=True)
    (channel_audio / 'canal_track.mp3').write_bytes(b'channel_audio')

    global_audio = tmp_path / 'audio'
    global_audio.mkdir(parents=True)
    (global_audio / 'global_track.mp3').write_bytes(b'global_audio')

    monkeypatch.setattr(media_assets, 'ASSETS_ROOT', tmp_path)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', channels_root)

    result = resolve_filesystem_media_assets(
        channel_slug='canal',
        video_format='longo',
        clip_id=0,
    )

    assert 'music' in result
    assert result['music']['name'] == 'canal_track.mp3'
    assert result['music']['absolute_path'] == str(channel_audio / 'canal_track.mp3')
    assert result['music']['music_volume'] == 0.24
