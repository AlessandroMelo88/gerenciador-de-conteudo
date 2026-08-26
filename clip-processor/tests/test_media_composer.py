from src.media_composer import compose_media


def test_compose_media_normalizes_segments_and_mixes_music(tmp_path, mocker):
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

    result = compose_media(str(input_path), str(output_path), 'curto', assets)

    assert result == str(output_path)
    assert normalize.call_count == 3
    concat.assert_called_once()
    mix.assert_called_once_with(
        mocker.ANY,
        str(music_path),
        mocker.ANY,
        0.2,
    )
    assert mix.call_args.args[0].endswith('/outro.mp4')
    assert mix.call_args.args[2].endswith('/outro_com_musica.mp4')
    copyfile.assert_called_once()
    assert str(copyfile.call_args.args[0]).endswith('/concatenated.mp4')
    assert copyfile.call_args.args[1] == str(output_path)


def test_compose_media_without_assets_keeps_input_path(tmp_path):
    input_path = tmp_path / 'clip.mp4'
    output_path = tmp_path / 'branded.mp4'
    input_path.write_bytes(b'fixture')

    assert compose_media(str(input_path), str(output_path), 'longo', {}) == str(input_path)
