"""Mídia por canal: biblioteca do painel x pasta do canal, formatos e degradação segura."""

from unittest.mock import MagicMock

import src.media_assets as media_assets
from src import video_processor
from src.media_assets import resolve_filesystem_media_assets, resolve_media_assets


def _conn_returning(rows_by_kind):
    """Conexão fake cujo SELECT devolve as linhas do `kind` pedido (1o parâmetro)."""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__.return_value = cursor
    cursor.__exit__.return_value = False

    def execute(_sql, params):
        cursor.fetchall.return_value = rows_by_kind.get(params[0], [])

    cursor.execute.side_effect = execute
    conn.cursor.return_value = cursor
    return conn


def _row(asset_id, kind, path, channel=7, fmt=None, priority=0, name='asset'):
    return {
        'id': asset_id,
        'kind': kind,
        'name': name,
        'path': path,
        'destination_channel_id': channel,
        'format': fmt,
        'priority': priority,
    }


# ---------------------------------------------------------------------------
# Resolução
# ---------------------------------------------------------------------------


def test_media_format_enabled_defaults_to_longo_only(monkeypatch):
    monkeypatch.delenv('MEDIA_FORMATS', raising=False)

    assert media_assets.media_format_enabled('longo') is True
    assert media_assets.media_format_enabled('curto') is False
    assert media_assets.media_format_enabled(None) is False


def test_media_format_enabled_reads_env(monkeypatch):
    monkeypatch.setenv('MEDIA_FORMATS', ' longo , CURTO ')

    assert media_assets.media_format_enabled('curto') is True


def test_panel_library_wins_over_channel_folder(tmp_path, monkeypatch):
    branding = tmp_path / 'branding'
    (branding / 'media' / 'intro').mkdir(parents=True)
    (branding / 'media' / 'intro' / 'a.mp4').write_bytes(b'x')
    channel_root = tmp_path / 'assets' / 'channels' / 'canal-a'
    channel_root.mkdir(parents=True)
    (channel_root / 'intro.mp4').write_bytes(b'folder')
    (channel_root / 'encerramento.mp4').write_bytes(b'folder')
    monkeypatch.setattr(media_assets, 'MEDIA_ROOT', branding)
    monkeypatch.setattr(media_assets, 'ASSETS_ROOT', tmp_path / 'assets')
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', tmp_path / 'assets' / 'channels')
    conn = _conn_returning(
        {'intro': [_row(1, 'intro', 'media/intro/a.mp4', name='Intro painel')]}
    )

    result = resolve_media_assets(
        conn, destination_channel_id=7, video_format='longo', clip_id=1, channel_slug='canal-a'
    )

    assert result['intro']['name'] == 'Intro painel'
    assert result['intro']['absolute_path'] == str(branding / 'media' / 'intro' / 'a.mp4')
    # o que o painel não configurou vem da pasta do canal
    assert result['outro']['source'] == 'filesystem'


def test_panel_asset_with_missing_file_is_ignored_not_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(media_assets, 'MEDIA_ROOT', tmp_path / 'branding')
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', tmp_path / 'sem-canais')
    conn = _conn_returning({'music': [_row(2, 'music', 'media/music/sumiu.mp3')]})

    result = resolve_media_assets(
        conn, destination_channel_id=7, video_format='longo', clip_id=1, channel_slug=None
    )

    assert result == {}


def test_panel_asset_cannot_escape_branding_root(tmp_path, monkeypatch):
    branding = tmp_path / 'branding'
    branding.mkdir()
    (tmp_path / 'segredo.mp3').write_bytes(b'x')
    monkeypatch.setattr(media_assets, 'MEDIA_ROOT', branding)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', tmp_path / 'sem-canais')
    conn = _conn_returning({'music': [_row(3, 'music', '../segredo.mp3')]})

    assert (
        resolve_media_assets(conn, destination_channel_id=7, video_format='longo', clip_id=1) == {}
    )


def test_resolve_media_assets_ignores_other_channels_and_global_assets(tmp_path, monkeypatch):
    branding = tmp_path / 'branding'
    (branding / 'm').mkdir(parents=True)
    (branding / 'm' / 'a.mp4').write_bytes(b'x')
    monkeypatch.setattr(media_assets, 'MEDIA_ROOT', branding)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', tmp_path / 'sem-canais')
    conn = _conn_returning(
        {
            'intro': [
                _row(1, 'intro', 'm/a.mp4', channel=None),
                _row(2, 'intro', 'm/a.mp4', channel=99),
            ]
        }
    )

    assert (
        resolve_media_assets(conn, destination_channel_id=7, video_format='longo', clip_id=1) == {}
    )


def test_resolve_media_assets_shorts_optin_via_env(tmp_path, monkeypatch):
    monkeypatch.setenv('MEDIA_FORMATS', 'longo,curto')
    channels_root = tmp_path / 'channels'
    channel_root = channels_root / 'canal-a'
    channel_root.mkdir(parents=True)
    (channel_root / 'intro.jpg').write_bytes(b'x')
    monkeypatch.setattr(media_assets, 'ASSETS_ROOT', tmp_path)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', channels_root)
    conn = _conn_returning({})

    result = resolve_media_assets(
        conn, destination_channel_id=7, video_format='curto', clip_id=1, channel_slug='canal-a'
    )

    assert 'intro' in result


def test_channel_slug_cannot_escape_channels_root(tmp_path, monkeypatch):
    channels_root = tmp_path / 'channels'
    channels_root.mkdir()
    (tmp_path / 'intro.mp4').write_bytes(b'x')
    monkeypatch.setattr(media_assets, 'ASSETS_ROOT', tmp_path)
    monkeypatch.setattr(media_assets, 'CHANNELS_ROOT', channels_root)

    for slug in ('..', '../', 'a/../..', '/etc'):
        assert (
            resolve_filesystem_media_assets(channel_slug=slug, video_format='longo', clip_id=0)
            == {}
        )


# ---------------------------------------------------------------------------
# Aplicação no corte: nunca derruba o clip
# ---------------------------------------------------------------------------


def _clip():
    return {'destination_channel_id': 7, 'destination_channel_slug': 'canal-a'}


def test_apply_channel_media_keeps_clip_when_no_assets(tmp_path, mocker):
    mocker.patch.object(video_processor, 'CLIPS_DIR', str(tmp_path))
    mocker.patch.object(video_processor, 'resolve_media_assets', return_value={})
    compose = mocker.patch.object(video_processor, 'compose_media')
    final = tmp_path / '1.mp4'
    final.write_bytes(b'original')

    assert video_processor.apply_channel_media(MagicMock(), _clip(), 1, 'longo', str(final)) is False
    compose.assert_not_called()
    assert final.read_bytes() == b'original'


def test_apply_channel_media_replaces_final_clip_with_branded_version(tmp_path, mocker):
    mocker.patch.object(video_processor, 'CLIPS_DIR', str(tmp_path))
    mocker.patch.object(
        video_processor, 'resolve_media_assets', return_value={'intro': {'absolute_path': 'x'}}
    )
    final = tmp_path / '1.mp4'
    final.write_bytes(b'original')

    def fake_compose(inp, out, fmt, assets):
        with open(out, 'wb') as f:
            f.write(b'branded')
        return out

    mocker.patch.object(video_processor, 'compose_media', side_effect=fake_compose)

    assert video_processor.apply_channel_media(MagicMock(), _clip(), 1, 'longo', str(final)) is True
    assert final.read_bytes() == b'branded'
    assert not (tmp_path / '1_branded.mp4').exists()


def test_apply_channel_media_ffmpeg_failure_keeps_original_and_cleans_partial(tmp_path, mocker):
    mocker.patch.object(video_processor, 'CLIPS_DIR', str(tmp_path))
    mocker.patch.object(
        video_processor, 'resolve_media_assets', return_value={'intro': {'absolute_path': 'x'}}
    )
    final = tmp_path / '1.mp4'
    final.write_bytes(b'original')
    partial = tmp_path / '1_branded.mp4'

    def boom(inp, out, fmt, assets):
        partial.write_bytes(b'meio')
        raise RuntimeError('ffmpeg quebrou')

    mocker.patch.object(video_processor, 'compose_media', side_effect=boom)

    assert video_processor.apply_channel_media(MagicMock(), _clip(), 1, 'longo', str(final)) is False
    assert final.read_bytes() == b'original'
    assert not partial.exists()


def test_apply_channel_media_resolver_failure_never_raises(tmp_path, mocker):
    mocker.patch.object(video_processor, 'CLIPS_DIR', str(tmp_path))
    mocker.patch.object(
        video_processor, 'resolve_media_assets', side_effect=RuntimeError('db caiu')
    )
    final = tmp_path / '1.mp4'
    final.write_bytes(b'original')

    assert video_processor.apply_channel_media(MagicMock(), _clip(), 1, 'longo', str(final)) is False
    assert final.read_bytes() == b'original'


def test_apply_channel_media_rejects_empty_composition(tmp_path, mocker):
    mocker.patch.object(video_processor, 'CLIPS_DIR', str(tmp_path))
    mocker.patch.object(
        video_processor, 'resolve_media_assets', return_value={'intro': {'absolute_path': 'x'}}
    )
    final = tmp_path / '1.mp4'
    final.write_bytes(b'original')

    def empty(inp, out, fmt, assets):
        open(out, 'wb').close()
        return out

    mocker.patch.object(video_processor, 'compose_media', side_effect=empty)

    assert video_processor.apply_channel_media(MagicMock(), _clip(), 1, 'longo', str(final)) is False
    assert final.read_bytes() == b'original'


def test_apply_channel_media_shorts_do_not_touch_database(tmp_path, mocker, monkeypatch):
    monkeypatch.delenv('MEDIA_FORMATS', raising=False)
    mocker.patch.object(video_processor, 'CLIPS_DIR', str(tmp_path))
    conn = MagicMock()
    final = tmp_path / '1.mp4'
    final.write_bytes(b'original')

    assert video_processor.apply_channel_media(conn, _clip(), 1, 'curto', str(final)) is False
    conn.cursor.assert_not_called()
