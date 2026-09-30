from pathlib import Path

from src.media_composer import _concat_segments, compose_media


def test_concat_segments_builds_video_and_audio_crossfades(tmp_path, mocker):
    segments = [tmp_path / 'intro.mp4', tmp_path / 'clip.mp4', tmp_path / 'outro.mp4']
    for segment in segments:
        segment.write_bytes(b'fixture')

    mocker.patch('src.media_composer._probe_duration', side_effect=[3.0, 10.0, 4.0])
    run_ffmpeg = mocker.patch('src.media_composer._run_ffmpeg')

    _concat_segments(segments, tmp_path / 'segments.txt', str(tmp_path / 'output.mp4'))

    command = run_ffmpeg.call_args.args[0]
    filter_graph = command[command.index('-filter_complex') + 1]
    assert 'xfade=transition=fade:duration=0.350:offset=2.650' in filter_graph
    assert 'acrossfade=d=0.350' in filter_graph
    assert filter_graph.count('xfade=transition=fade') == 2
    assert command[command.index('-map') + 1] == '[vx2]'
    assert command[command.index('-map', command.index('-map') + 1) + 1] in {'[anorm]', '[ax2]'}


def test_compose_media_applies_related_card_only_to_outro(tmp_path, mocker):
    input_path = tmp_path / 'clip.mp4'
    intro_path = tmp_path / 'intro.jpg'
    outro_path = tmp_path / 'outro.jpg'
    output_path = tmp_path / 'branded.mp4'
    for path in (input_path, intro_path, outro_path):
        path.write_bytes(b'fixture')

    mocker.patch('src.media_composer._normalize_segment')
    card = mocker.patch('src.media_composer._apply_related_video_card', return_value=True)
    mocker.patch('src.media_composer._concat_segments')
    mocker.patch('src.media_composer.shutil.copyfile')

    compose_media(
        str(input_path),
        str(output_path),
        'longo',
        {
            'intro': {'absolute_path': str(intro_path)},
            'outro': {'absolute_path': str(outro_path)},
            'related_video': {
                'video_id': 'published123',
                'title': 'Próximo assunto',
            },
        },
    )

    card.assert_called_once()
    assert Path(card.call_args.args[0]).name == 'outro.mp4'
    assert card.call_args.args[2] == 'longo'
    assert card.call_args.args[3]['video_id'] == 'published123'
