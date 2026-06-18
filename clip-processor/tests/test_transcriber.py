"""
test_transcriber.py — Testes unitários para transcriber.py (AI-01).

Estado inicial: RED — todos falham com NotImplementedError.
Após implementação: GREEN.
"""
import pytest
from unittest.mock import MagicMock, patch
from src.transcriber import transcribe_video, save_transcript


class TestTranscribeVideo:

    def test_transcription_returns_segments(self, mock_db_conn, sample_video_id, tmp_path):
        """AI-01: Groq Whisper retorna dict com texto e lista de segmentos com start/end/text."""
        # Criar arquivo MP4 falso pequeno (<25MB) para não acionar extração de áudio
        video_path = str(tmp_path / f'{sample_video_id}.mp4')
        with open(video_path, 'wb') as f:
            f.write(b'fake_mp4_content')

        # Mock do cliente Groq retornando segmentos com estrutura verbose_json
        mock_seg = MagicMock()
        mock_seg.start = 0.0
        mock_seg.end = 5.5
        mock_seg.text = 'Gol do Vini Jr na prorrogação!'

        mock_groq = MagicMock()
        mock_groq.audio.transcriptions.create.return_value = MagicMock(
            text='Gol do Vini Jr na prorrogação!',
            segments=[mock_seg],
        )

        result = transcribe_video(sample_video_id, video_path, groq_client=mock_groq)

        assert result is not None
        assert result['video_id'] == sample_video_id
        assert 'segments' in result
        assert len(result['segments']) == 1
        assert result['segments'][0]['start'] == 0.0
        assert result['segments'][0]['end'] == 5.5
        assert 'Vini' in result['segments'][0]['text']

    def test_transcript_saved_to_disk(self, mock_db_conn, sample_video_id, tmp_path):
        """AI-01: save_transcript() cria arquivo {video_id}_transcript.json em disco."""
        transcript = {
            'video_id': sample_video_id,
            'text': 'Texto completo',
            'segments': [{'start': 0.0, 'end': 5.0, 'text': 'Texto'}],
        }

        with patch('src.transcriber.VIDEOS_DIR', str(tmp_path)):
            path = save_transcript(mock_db_conn, sample_video_id, transcript)

        import os, json
        assert os.path.exists(path)
        with open(path) as f:
            saved = json.load(f)
        assert saved['video_id'] == sample_video_id

    def test_transcript_path_updated_in_db(self, mock_db_conn, sample_video_id, tmp_path):
        """AI-01: save_transcript() atualiza transcript_path em source_videos no banco."""
        transcript = {
            'video_id': sample_video_id,
            'text': 'Texto',
            'segments': [],
        }

        with patch('src.transcriber.VIDEOS_DIR', str(tmp_path)):
            save_transcript(mock_db_conn, sample_video_id, transcript)

        # Verificar que UPDATE foi chamado com transcript_path e video_id
        mock_db_conn.cursor().__enter__().execute.assert_called()
        call_args = mock_db_conn.cursor().__enter__().execute.call_args
        sql = call_args[0][0]
        assert 'transcript_path' in sql
        assert 'source_videos' in sql

    def test_large_file_audio_extraction(self, mock_db_conn, sample_video_id, tmp_path):
        """AI-01: Arquivo >24MB aciona extração de áudio MP3 via ffmpeg antes de chamar Groq."""
        # Criar arquivo falso grande (>24MB simulado via mock de os.path.getsize)
        video_path = str(tmp_path / f'{sample_video_id}.mp4')
        with open(video_path, 'wb') as f:
            f.write(b'x')

        mock_seg = MagicMock()
        mock_seg.start = 0.0
        mock_seg.end = 10.0
        mock_seg.text = 'Podcast longo'

        mock_groq = MagicMock()
        mock_groq.audio.transcriptions.create.return_value = MagicMock(
            text='Podcast longo',
            segments=[mock_seg],
        )

        with patch('os.path.getsize', return_value=25_000_000), \
             patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = transcribe_video(sample_video_id, video_path, groq_client=mock_groq)

        # ffmpeg deve ter sido chamado para extração de áudio
        mock_run.assert_called_once()
        ffmpeg_cmd = mock_run.call_args[0][0]
        assert 'ffmpeg' in ffmpeg_cmd
        assert '-vn' in ffmpeg_cmd  # sem vídeo — só áudio

    def test_api_failure_marks_video_failed(self, mock_db_conn, sample_video_id, tmp_path):
        """AI-01: Falha na API Groq retorna None (chamador marca vídeo como failed)."""
        video_path = str(tmp_path / f'{sample_video_id}.mp4')
        with open(video_path, 'wb') as f:
            f.write(b'fake')

        mock_groq = MagicMock()
        mock_groq.audio.transcriptions.create.side_effect = Exception('API timeout')

        result = transcribe_video(sample_video_id, video_path, groq_client=mock_groq)

        assert result is None
