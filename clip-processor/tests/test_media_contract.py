import json
from types import SimpleNamespace

import pytest

from src.media_contract import MediaContractError, validate_short_media
from src.video_processor import render_short_clip


def _ffprobe_result(duration=30.0, width=1080, height=1920):
    return SimpleNamespace(
        stdout=json.dumps(
            {
                'streams': [{'codec_type': 'video', 'width': width, 'height': height}],
                'format': {'duration': str(duration)},
            }
        ),
        stderr='',
    )


def test_short_media_contract_accepts_vertical_30s_file(mocker, tmp_path):
    mocker.patch('src.media_contract.subprocess.run', return_value=_ffprobe_result())

    info = validate_short_media(str(tmp_path / 'short.mp4'))

    assert info['duration'] == 30.0
    assert info['is_vertical'] is True


@pytest.mark.parametrize(
    ('duration', 'width', 'height', 'message'),
    [
        (29.0, 1080, 1920, 'entre 30 e 45s'),
        (30.0, 1920, 1080, 'precisa ser vertical 9:16'),
    ],
)
def test_short_media_contract_rejects_invalid_file(
    mocker, tmp_path, duration, width, height, message
):
    mocker.patch(
        'src.media_contract.subprocess.run',
        return_value=_ffprobe_result(duration=duration, width=width, height=height),
    )

    with pytest.raises(MediaContractError, match=message):
        validate_short_media(str(tmp_path / 'short.mp4'))


def test_render_short_clip_composes_subtitle_and_watermark_in_one_ffmpeg_call(mocker, tmp_path):
    mock_run = mocker.patch('src.video_processor.subprocess.run')
    watermark = tmp_path / 'watermark.png'
    watermark.touch()
    srt = tmp_path / 'short.srt'
    srt.write_text('1\n00:00:00,000 --> 00:00:01,000\nTexto\n', encoding='utf-8')

    output = tmp_path / 'short.mp4'
    assert render_short_clip(
        '/app/videos/source.mp4',
        100.0,
        130.0,
        str(output),
        subtitle_path=str(srt),
        watermark_path=str(watermark),
    ) == str(output)

    assert mock_run.call_count == 1
    command = mock_run.call_args.args[0]
    assert command[command.index('-t') + 1] == '30.00'
    assert command[command.index('-map') + 1] == '[short_final]'
    assert command.count('-c:v') == 1
    filter_graph = command[command.index('-filter_complex') + 1]
    assert 'subtitles=' in filter_graph
    assert 'overlay=W-w-20:20' in filter_graph
