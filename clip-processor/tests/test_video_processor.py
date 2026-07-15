"""
test_video_processor.py — Testes Phase 4 VID-01, VID-02, VID-03.

Estado inicial do Plan 04-01: RED controlado por NotImplementedError.
"""
import json

import pytest

from src.video_processor import (
    burn_subtitles,
    cut_clip,
    extract_thumbnail,
    generate_srt,
    process_clip,
)


SAMPLE_TRANSCRIPT = {
    'video_id': 'vid001aaaaaa',
    'text': 'Texto completo',
    'segments': [
        {'start': 100.0, 'end': 103.2, 'text': 'Primeira fala do corte'},
        {'start': 104.0, 'end': 108.5, 'text': 'Segunda fala importante'},
        {'start': 130.0, 'end': 140.0, 'text': 'Fora do clip'},
    ],
}


class TestVideoProcessor:

    def test_cut_clip_uses_ffmpeg_with_exact_timestamps(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')
        output = tmp_path / 'clip.mp4'

        result = cut_clip('/app/videos/source.mp4', 100.0, 220.0, str(output))

        assert result == str(output)
        cmd = mock_run.call_args.args[0]
        assert '-ss' in cmd
        assert cmd[cmd.index('-ss') + 1] == '100.0'
        assert '-to' in cmd
        assert cmd[cmd.index('-to') + 1] == '220.0'

    def test_cut_clip_outputs_1080x1920_filter(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')
        output = tmp_path / 'clip.mp4'

        cut_clip('/app/videos/source.mp4', 0.0, 60.0, str(output))

        cmd = mock_run.call_args.args[0]
        filter_arg = cmd[cmd.index('-vf') + 1]
        assert 'scale=1080:1920' in filter_arg
        assert 'crop=1080:1920' in filter_arg
        assert 'setsar=1' in filter_arg

    def test_thumbnail_extracted_from_clip(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')
        thumbnail = tmp_path / 'thumb.jpg'

        result = extract_thumbnail('/app/clips/1.mp4', str(thumbnail), at_seconds=3.0)

        assert result == str(thumbnail)
        cmd = mock_run.call_args.args[0]
        assert '-frames:v' in cmd
        assert '1' in cmd
        assert str(thumbnail) in cmd

    def test_process_clip_updates_paths_and_status(self, tmp_path, mock_db_conn, mocker):
        transcript_path = tmp_path / 'transcript.json'
        transcript_path.write_text(json.dumps(SAMPLE_TRANSCRIPT), encoding='utf-8')

        clip_row = {
            'id': 10,
            'source_video_id': 1,
            'youtube_video_id': 'vid001aaaaaa',
            'source_title': 'Debate quente sobre final',
            'local_path': '/app/videos/source.mp4',
            'transcript_path': str(transcript_path),
            'start_time': 100.0,
            'end_time': 220.0,
            'score': 9,
            'reason': 'Debate acalorado',
            'destination_channel_slug': None,  # sem canal-destino: usa os.rename
        }
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = clip_row

        mocker.patch('src.video_processor.cut_clip', return_value='/app/clips/10_raw.mp4')
        mocker.patch('src.video_processor.generate_srt', return_value='/app/clips/10.srt')
        mocker.patch('src.video_processor.burn_subtitles', return_value='/app/clips/10_subtitled.mp4')
        mocker.patch('src.video_processor.extract_thumbnail', return_value='/app/thumbnails/10.jpg')
        mocker.patch('src.video_processor.generate_metadata', return_value={
            'title': 'Titulo',
            'description': 'Descricao',
            'tags': ['futebol'],
        })
        mocker.patch('src.video_processor.update_clip_metadata')
        mocker.patch('src.video_processor.os.rename')  # slug=None → rename subtitled → final

        assert process_clip(mock_db_conn, 10) is True
        execute_calls = [str(call) for call in cursor.execute.call_args_list]
        assert any('clip_path' in call and 'thumbnail_path' in call for call in execute_calls)
        assert any("status='pending'" in call or 'pending' in call for call in execute_calls)

    def test_process_clip_failure_marks_failed(self, mock_db_conn, mocker):
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {
            'id': 10,
            'local_path': '/app/videos/source.mp4',
            'transcript_path': '/missing/transcript.json',
            'start_time': 0.0,
            'end_time': 60.0,
            'reason': 'Motivo',
            'score': 8,
            'source_title': 'Titulo',
            'destination_channel_slug': None,
        }
        mocker.patch('src.video_processor.cut_clip', side_effect=RuntimeError('ffmpeg failed'))

        assert process_clip(mock_db_conn, 10) is False
        execute_calls = [str(call) for call in cursor.execute.call_args_list]
        assert any('failed' in call for call in execute_calls)


class TestSubtitles:

    def test_srt_contains_shifted_segment_times(self, tmp_path):
        srt_path = tmp_path / 'clip.srt'

        result = generate_srt(SAMPLE_TRANSCRIPT, 100.0, 110.0, str(srt_path))

        assert result == str(srt_path)
        content = srt_path.read_text(encoding='utf-8')
        assert '00:00:00,000 --> 00:00:03,200' in content
        assert 'Primeira fala do corte' in content
        assert 'Fora do clip' not in content

    def test_burn_subtitles_uses_force_style(self, tmp_path, mocker):
        mock_run = mocker.patch('src.video_processor.subprocess.run')
        output = tmp_path / 'final.mp4'

        result = burn_subtitles('/app/clips/raw.mp4', '/app/clips/clip.srt', str(output))

        assert result == str(output)
        cmd = mock_run.call_args.args[0]
        filter_arg = cmd[cmd.index('-vf') + 1]
        assert 'subtitles=' in filter_arg
        assert 'force_style=' in filter_arg
        assert 'Outline=1' in filter_arg
        assert 'Alignment=2' in filter_arg
        assert 'Fontsize=38' in filter_arg


# ---------------------------------------------------------------------------
# Wave 2 — RED tests: Overlay Watermark (COPY-01)
# Estes testes falham até a implementação em Wave 3-4.
# ---------------------------------------------------------------------------

class TestOverlayWatermark:
    """Testes RED para overlay_watermark (COPY-01)."""

    def test_watermark_present_calls_ffmpeg_with_filter_complex(self, tmp_path, mocker):
        """COPY-01: wm_path existente → ffmpeg com -filter_complex e overlay=W-w-20:20."""
        from src.video_processor import overlay_watermark

        mock_run = mocker.patch('src.video_processor.subprocess.run')
        mocker.patch('os.path.exists', return_value=True)

        output = tmp_path / 'watermarked.mp4'
        result = overlay_watermark(
            '/app/clips/clip.mp4',
            '/app/assets/watermark.png',
            str(output),
        )

        assert result == str(output)
        cmd = mock_run.call_args.args[0]
        assert '-filter_complex' in cmd
        filter_val = cmd[cmd.index('-filter_complex') + 1]
        assert 'overlay=W-w-20:20' in filter_val

    def test_watermark_missing_returns_input_path_without_ffmpeg(self, tmp_path, mocker):
        """COPY-01: wm_path ausente → retorna input_path sem chamar subprocess."""
        from src.video_processor import overlay_watermark

        mock_run = mocker.patch('src.video_processor.subprocess.run')
        mocker.patch('os.path.exists', return_value=False)

        output = tmp_path / 'watermarked.mp4'
        result = overlay_watermark(
            '/app/clips/clip.mp4',
            '/app/assets/missing_watermark.png',
            str(output),
        )

        # Deve retornar o caminho de entrada sem modificação
        assert result == '/app/clips/clip.mp4'
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# Wave 4 — Integration tests: process_clip com overlay_watermark (MCAN-02)
# ---------------------------------------------------------------------------

class TestProcessClipWithWatermark:
    """Testes de integração: process_clip aplica overlay_watermark com slug do canal-destino."""

    def test_process_clip_calls_overlay_watermark_with_slug(self, tmp_path, mock_db_conn, mocker):
        """MCAN-02: process_clip chama overlay_watermark com watermark_path derivado do slug."""
        transcript_path = tmp_path / 'transcript.json'
        transcript_path.write_text(json.dumps(SAMPLE_TRANSCRIPT), encoding='utf-8')

        clip_row = {
            'id': 20,
            'source_video_id': 1,
            'youtube_video_id': 'vid002bbbbbb',
            'source_title': 'Debate quente',
            'local_path': '/app/videos/source.mp4',
            'transcript_path': str(transcript_path),
            'start_time': 100.0,
            'end_time': 220.0,
            'score': 9,
            'reason': 'Debate acalorado',
            'destination_channel_slug': 'futebol-br',
        }
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = clip_row

        mocker.patch('src.video_processor.cut_clip', return_value='/app/clips/20_raw.mp4')
        mocker.patch('src.video_processor.generate_srt', return_value='/app/clips/20.srt')
        mocker.patch('src.video_processor.burn_subtitles', return_value='/app/clips/20_subtitled.mp4')
        mock_watermark = mocker.patch('src.video_processor.overlay_watermark', return_value='/app/clips/20.mp4')
        mocker.patch('src.video_processor.extract_thumbnail', return_value='/app/thumbnails/20.jpg')
        mocker.patch('src.video_processor.generate_metadata', return_value={
            'title': 'Titulo', 'description': 'Desc', 'tags': ['futebol'],
        })
        mocker.patch('src.video_processor.update_clip_metadata')
        mocker.patch('src.video_processor.os.remove')

        result = process_clip(mock_db_conn, 20)

        assert result is True
        mock_watermark.assert_called_once()
        call_args = mock_watermark.call_args
        assert '/app/branding/watermark-futebol-br.png' in call_args.args or \
               '/app/branding/watermark-futebol-br.png' in str(call_args), \
               f'overlay_watermark deve receber watermark-futebol-br.png. Args: {call_args}'

    def test_process_clip_skips_watermark_when_slug_is_null(self, tmp_path, mock_db_conn, mocker):
        """MCAN-02: destination_channel_slug NULL → os.rename é usado, overlay_watermark NÃO chamado."""
        transcript_path = tmp_path / 'transcript.json'
        transcript_path.write_text(json.dumps(SAMPLE_TRANSCRIPT), encoding='utf-8')

        clip_row = {
            'id': 21,
            'source_video_id': 1,
            'youtube_video_id': 'vid003cccccc',
            'source_title': 'Jogo sem canal destino',
            'local_path': '/app/videos/source.mp4',
            'transcript_path': str(transcript_path),
            'start_time': 100.0,
            'end_time': 220.0,
            'score': 8,
            'reason': 'Moment sem canal',
            'destination_channel_slug': None,
        }
        cursor = mock_db_conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = clip_row

        mocker.patch('src.video_processor.cut_clip', return_value='/app/clips/21_raw.mp4')
        mocker.patch('src.video_processor.generate_srt', return_value='/app/clips/21.srt')
        mocker.patch('src.video_processor.burn_subtitles', return_value='/app/clips/21_subtitled.mp4')
        mock_watermark = mocker.patch('src.video_processor.overlay_watermark')
        mocker.patch('src.video_processor.extract_thumbnail', return_value='/app/thumbnails/21.jpg')
        mocker.patch('src.video_processor.generate_metadata', return_value={
            'title': 'Titulo', 'description': 'Desc', 'tags': [],
        })
        mocker.patch('src.video_processor.update_clip_metadata')
        mock_rename = mocker.patch('src.video_processor.os.rename')

        result = process_clip(mock_db_conn, 21)

        assert result is True
        mock_watermark.assert_not_called()
        mock_rename.assert_called_once()
