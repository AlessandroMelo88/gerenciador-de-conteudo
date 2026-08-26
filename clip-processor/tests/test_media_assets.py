from unittest.mock import MagicMock

from src.media_assets import choose_media_asset, resolve_media_assets


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
        {'id': 10, 'destination_channel_id': None, 'format': None, 'priority': 1},
        {'id': 11, 'destination_channel_id': None, 'format': None, 'priority': 5},
    ]

    result = choose_media_asset(
        candidates,
        destination_channel_id=None,
        video_format='longo',
        clip_id=99,
    )

    assert result == candidates[1]


def test_choose_media_asset_rotates_equivalent_assets_by_clip_id():
    candidates = [
        {'id': 20, 'destination_channel_id': None, 'format': None, 'priority': 0},
        {'id': 21, 'destination_channel_id': None, 'format': None, 'priority': 0},
    ]

    result = choose_media_asset(
        candidates,
        destination_channel_id=None,
        video_format='curto',
        clip_id=1,
    )

    assert result == candidates[1]


def test_resolve_media_assets_rolls_back_optional_table_failure():
    """A ausência da tabela opcional não pode abortar a transação do clip."""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = False
    cursor.execute.side_effect = RuntimeError('media_assets does not exist')
    conn.cursor.return_value = cursor

    result = resolve_media_assets(
        conn,
        destination_channel_id=None,
        video_format='longo',
        clip_id=84,
    )

    assert result == {}
    assert conn.rollback.call_count == 3
