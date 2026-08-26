"""Testes unitários para transcriber.py (AI-01)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.transcriber import (
    _download_youtube_player_transcript,
    _download_youtube_transcript,
    _parse_vtt,
    _parse_youtube_timedtext,
    save_transcript,
    transcribe_video,
)


@pytest.fixture(autouse=True)
def no_network_caption_lookup(monkeypatch):
    """Os testes do fallback Groq não devem consultar o YouTube real."""
    monkeypatch.setattr('src.transcriber._download_youtube_transcript', lambda _video_id: None)


class TestTranscribeVideo:
    def test_parse_youtube_timedtext_returns_timestamped_segments(self):
        payload = """<?xml version="1.0" encoding="utf-8" ?>
<timedtext><body>
<p t="1000" d="1500"><s>Olá &amp;</s><s t="500"> mundo</s></p>
<p t="3000" d="1000">Segundo trecho</p>
</body></timedtext>"""

        result = _parse_youtube_timedtext(payload)

        assert result is not None
        assert result['text'] == 'Olá & mundo\nSegundo trecho'
        assert result['segments'] == [
            {'start': 1.0, 'end': 2.5, 'text': 'Olá & mundo'},
            {'start': 3.0, 'end': 4.0, 'text': 'Segundo trecho'},
        ]

    def test_player_transcript_prefers_manual_portuguese_caption(self, sample_video_id):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return self.payload

        page = b'<html>"INNERTUBE_API_KEY":"test-key"</html>'
        player_response = {
            'captions': {
                'playerCaptionsTracklistRenderer': {
                    'captionTracks': [
                        {
                            'baseUrl': 'https://caption/automatic',
                            'languageCode': 'pt',
                            'kind': 'asr',
                        },
                        {
                            'baseUrl': 'https://caption/manual',
                            'languageCode': 'pt-BR',
                        },
                    ]
                }
            }
        }
        caption = b'<timedtext><body><p t="0" d="3000">Legenda publicada</p></body></timedtext>'

        def fake_urlopen(request, timeout):
            assert timeout == 20
            if request.full_url.endswith(f'watch?v={sample_video_id}'):
                return FakeResponse(page)
            if 'youtubei/v1/player' in request.full_url:
                return FakeResponse(json.dumps(player_response).encode())
            assert request.full_url == 'https://caption/manual'
            return FakeResponse(caption)

        with patch('src.transcriber.urlopen', side_effect=fake_urlopen):
            result = _download_youtube_player_transcript(sample_video_id)

        assert result is not None
        assert result['source'] == 'youtube_captions'
        assert result['segments'][0]['text'] == 'Legenda publicada'

    def test_parse_vtt_returns_timestamped_segments(self):
        payload = """WEBVTT

00:00.000 --> 00:02.500
Olá &amp; mundo <c>teste</c>

00:02.500 --> 00:05.000 align:start position:0%
Segundo trecho
"""

        result = _parse_vtt(payload)

        assert result is not None
        assert result['text'] == 'Olá & mundo teste\nSegundo trecho'
        assert result['segments'] == [
            {'start': 0.0, 'end': 2.5, 'text': 'Olá & mundo teste'},
            {'start': 2.5, 'end': 5.0, 'text': 'Segundo trecho'},
        ]

    def test_youtube_caption_precedes_groq(self, sample_video_id):
        youtube_transcript = {
            'video_id': sample_video_id,
            'text': 'Transcrição oficial',
            'segments': [{'start': 0.0, 'end': 5.0, 'text': 'Transcrição oficial'}],
            'source': 'youtube_captions',
        }
        mock_groq = MagicMock()

        with patch(
            'src.transcriber._download_youtube_transcript', return_value=youtube_transcript
        ) as download_caption:
            result = transcribe_video(sample_video_id, '/does/not/matter.mp4', mock_groq)

        assert result == youtube_transcript
        download_caption.assert_called_once_with(sample_video_id)
        mock_groq.audio.transcriptions.create.assert_not_called()

    def test_youtube_caption_does_not_create_groq_client(self, sample_video_id):
        youtube_transcript = {
            'video_id': sample_video_id,
            'text': 'Transcrição publicada',
            'segments': [{'start': 0.0, 'end': 5.0, 'text': 'Transcrição publicada'}],
            'source': 'youtube_captions',
        }

        with (
            patch('src.transcriber._download_youtube_transcript', return_value=youtube_transcript),
            patch('groq.Groq') as groq_factory,
        ):
            result = transcribe_video(sample_video_id, '/does/not/matter.mp4')

        assert result == youtube_transcript
        groq_factory.assert_not_called()

    def test_download_youtube_caption_falls_back_to_automatic(self, tmp_path, sample_video_id):
        options_seen = []

        class FakeYoutubeDL:
            def __init__(self, options):
                self.options = options
                options_seen.append(options)

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def download(self, urls):
                assert urls == [f'https://www.youtube.com/watch?v={sample_video_id}']
                if self.options['writeautomaticsub']:
                    caption_path = Path(
                        self.options['outtmpl']
                        .replace('%(id)s', sample_video_id)
                        .replace('%(ext)s', 'vtt')
                    )
                    caption_path.write_text(
                        'WEBVTT\n\n00:00.000 --> 00:03.000\nLegenda automática\n',
                        encoding='utf-8',
                    )

        with (
            patch('src.transcriber.VIDEOS_DIR', str(tmp_path)),
            patch('src.transcriber._download_youtube_player_transcript', return_value=None),
            patch('src.transcriber.yt_dlp.YoutubeDL', FakeYoutubeDL),
        ):
            result = _download_youtube_transcript(sample_video_id)

        assert result is not None
        assert result['source'] == 'youtube_automatic_captions'
        assert result['segments'][0]['text'] == 'Legenda automática'
        assert options_seen[0]['writesubtitles'] is True
        assert options_seen[0]['writeautomaticsub'] is False
        assert options_seen[1]['writesubtitles'] is False
        assert options_seen[1]['writeautomaticsub'] is True

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

        import json
        import os

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

        with patch('os.path.getsize', return_value=25_000_000), patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            transcribe_video(sample_video_id, video_path, groq_client=mock_groq)

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
