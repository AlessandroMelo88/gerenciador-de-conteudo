"""Contratos dos perfis de velocidade do encoder FFmpeg."""

from src.video_quality import ffmpeg_global_options, video_encoder_options, video_render_mode


def _value_after(options: tuple[str, ...], flag: str) -> str:
    return options[options.index(flag) + 1]


def test_quality_mode_keeps_the_existing_manual_encoder_controls(monkeypatch):
    monkeypatch.delenv('VIDEO_RENDER_MODE', raising=False)
    monkeypatch.setenv('FFMPEG_PRESET', 'slow')
    monkeypatch.setenv('FFMPEG_CRF', '14')

    options = video_encoder_options()

    assert video_render_mode() == 'quality'
    assert _value_after(options, '-preset') == 'slow'
    assert _value_after(options, '-crf') == '14'
    assert _value_after(options, '-threads') == '0'
    assert ffmpeg_global_options() == ('-filter_threads', '0', '-filter_complex_threads', '0')


def test_fast_mode_prefers_a_faster_preset_and_auto_threads(monkeypatch):
    monkeypatch.setenv('VIDEO_RENDER_MODE', 'fast')
    monkeypatch.setenv('FFMPEG_PRESET', 'slow')
    monkeypatch.setenv('FFMPEG_CRF', '16')

    options = video_encoder_options()

    assert _value_after(options, '-preset') == 'veryfast'
    assert _value_after(options, '-crf') == '16'
    assert _value_after(options, '-threads') == '0'
    assert ffmpeg_global_options() == ('-filter_threads', '0', '-filter_complex_threads', '0')


def test_ultra_mode_uses_the_fastest_profile_without_losing_crf_control(monkeypatch):
    monkeypatch.setenv('VIDEO_RENDER_MODE', 'ultra')
    monkeypatch.setenv('FFMPEG_CRF', '18')

    options = video_encoder_options()

    assert _value_after(options, '-preset') == 'ultrafast'
    assert _value_after(options, '-crf') == '18'
    assert _value_after(options, '-threads') == '0'


def test_unknown_mode_falls_back_to_quality(monkeypatch):
    monkeypatch.setenv('VIDEO_RENDER_MODE', 'turbo-inexistente')
    monkeypatch.setenv('FFMPEG_PRESET', 'faster')

    options = video_encoder_options()

    assert video_render_mode() == 'quality'
    assert _value_after(options, '-preset') == 'faster'
    assert ffmpeg_global_options() == ('-filter_threads', '0', '-filter_complex_threads', '0')


def test_quality_mode_accepts_explicit_machine_thread_limits(monkeypatch):
    monkeypatch.setenv('VIDEO_RENDER_MODE', 'quality')
    monkeypatch.setenv('FFMPEG_THREADS', '10')
    monkeypatch.setenv('FFMPEG_FILTER_THREADS', '10')

    assert _value_after(video_encoder_options(), '-threads') == '10'
    assert ffmpeg_global_options() == (
        '-filter_threads',
        '10',
        '-filter_complex_threads',
        '10',
    )
