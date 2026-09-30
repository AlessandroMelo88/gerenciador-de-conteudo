from src.media_composer import _mix_music, _volume, compose_media


def test_compose_media_normalizes_longform_segments_and_mixes_music(tmp_path, mocker):
    input_path = tmp_path / 'clip.mp4'
    intro_path = tmp_path / 'intro.jpg'
    outro_path = tmp_path / 'outro.jpg'
    music_path = tmp_path / 'music.mp3'
    output_path = tmp_path / 'branded.mp4'
    for path in (input_path, intro_path, outro_path, music_path):
        path.write_bytes(b'fixture')

    normalize = mocker.patch('src.media_composer._normalize_segment')
    concat = mocker.patch('src.media_composer._concat_segments')
    mix = mocker.patch('src.media_composer._mix_music')
    copyfile = mocker.patch('src.media_composer.shutil.copyfile')

    assets = {
        'intro': {'absolute_path': str(intro_path), 'duration_seconds': 4},
        'outro': {'absolute_path': str(outro_path), 'duration_seconds': 5},
        'music': {'absolute_path': str(music_path), 'music_volume': 0.2},
    }

    result = compose_media(str(input_path), str(output_path), 'longo', assets)

    assert result == str(output_path)
    assert normalize.call_count == 3
    concat.assert_called_once()
    mix.assert_called_once_with(
        mocker.ANY,
        str(music_path),
        mocker.ANY,
        0.2,
    )
    assert mix.call_args.args[0].endswith('/concatenated.mp4')
    assert mix.call_args.args[2].endswith('/concatenated_com_musica.mp4')
    copyfile.assert_called_once()
    assert str(copyfile.call_args.args[0]).endswith('/concatenated_com_musica.mp4')
    assert copyfile.call_args.args[1] == str(output_path)


def test_mix_music_starts_at_configured_volume_and_ramps_to_full_volume(tmp_path, mocker):
    input_path = tmp_path / 'concatenated.mp4'
    music_path = tmp_path / 'music.mp3'
    output_path = tmp_path / 'with_music.mp4'
    input_path.write_bytes(b'fixture')
    music_path.write_bytes(b'fixture')

    mocker.patch('src.media_composer._probe_duration', return_value=30.0)
    run_ffmpeg = mocker.patch('src.media_composer._run_ffmpeg')

    _mix_music(str(input_path), str(music_path), str(output_path), 0.24)

    command = run_ffmpeg.call_args.args[0]
    filter_graph = command[command.index('-filter_complex') + 1]
    assert 'atrim=duration=15.000' in filter_graph
    assert (
        'if(lt(t,7.000),0.240,if(lt(t,15.000),0.240+(1-0.240)*(t-7.000)/8.000,1))' in filter_graph
    )
    assert 'adelay=15000|15000' in filter_graph
    assert 'dropout_transition=0' in filter_graph


def test_compose_media_ignores_assets_for_shorts(tmp_path, mocker):
    input_path = tmp_path / 'clip.mp4'
    output_path = tmp_path / 'branded.mp4'
    intro_path = tmp_path / 'intro.mp4'
    outro_path = tmp_path / 'outro.mp4'
    music_path = tmp_path / 'music.mp3'
    for path in (input_path, intro_path, outro_path, music_path):
        path.write_bytes(b'fixture')

    normalize = mocker.patch('src.media_composer._normalize_segment')
    concat = mocker.patch('src.media_composer._concat_segments')
    mix = mocker.patch('src.media_composer._mix_music')

    assets = {
        'intro': {'absolute_path': str(intro_path)},
        'outro': {'absolute_path': str(outro_path)},
        'music': {'absolute_path': str(music_path)},
    }

    assert compose_media(str(input_path), str(output_path), 'curto', assets) == str(input_path)
    normalize.assert_not_called()
    concat.assert_not_called()
    mix.assert_not_called()


def test_compose_media_without_assets_keeps_input_path(tmp_path):
    input_path = tmp_path / 'clip.mp4'
    output_path = tmp_path / 'branded.mp4'
    input_path.write_bytes(b'fixture')

    assert compose_media(str(input_path), str(output_path), 'longo', {}) == str(input_path)


def test_volume_accepts_decimal_from_postgres_and_falls_back_on_garbage():
    from decimal import Decimal

    assert _volume(Decimal('0.300')) == 0.3
    assert _volume(None) == 0.24
    assert _volume('lixo') == 0.24
    assert _volume(0) == 0.24


def test_compose_media_uses_shorts_when_format_is_enabled(tmp_path, mocker, monkeypatch):
    monkeypatch.setenv('MEDIA_FORMATS', 'longo,curto')
    input_path = tmp_path / 'clip.mp4'
    intro_path = tmp_path / 'intro.jpg'
    output_path = tmp_path / 'branded.mp4'
    for path in (input_path, intro_path):
        path.write_bytes(b'fixture')

    normalize = mocker.patch('src.media_composer._normalize_segment')
    mocker.patch('src.media_composer._concat_segments')
    mocker.patch('src.media_composer.shutil.copyfile')

    result = compose_media(
        str(input_path), str(output_path), 'curto', {'intro': {'absolute_path': str(intro_path)}}
    )

    assert result == str(output_path)
    assert normalize.call_count == 2
    assert normalize.call_args_list[0].args[2] == 'curto'


def test_compose_media_skips_missing_asset_files(tmp_path):
    input_path = tmp_path / 'clip.mp4'
    input_path.write_bytes(b'fixture')

    result = compose_media(
        str(input_path),
        str(tmp_path / 'branded.mp4'),
        'longo',
        {'intro': {'absolute_path': str(tmp_path / 'nao-existe.mp4')}},
    )

    assert result == str(input_path)
