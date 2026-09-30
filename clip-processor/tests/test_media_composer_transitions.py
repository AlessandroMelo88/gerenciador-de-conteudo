from src.media_composer import _concat_segments


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
