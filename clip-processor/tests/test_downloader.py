"""
Testes ACQU-02: download até 1080p, disk guard, partial cleanup.

Módulo alvo: src.downloader
Exports esperados: download_video(video_id, output_path) -> bool

Os cenários cobrem download, proteção de disco e limpeza de artefatos parciais.
"""

import os
import time
from typing import ClassVar

from src.downloader import cleanup_stale_downloads, download_video

MIN_FREE_SPACE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


def _mock_pause_check(mocker):
    """Evita que a suíte abra PostgreSQL real no hook de progresso do yt-dlp."""
    conn = mocker.MagicMock()
    conn.cursor.return_value.__enter__.return_value.fetchone.return_value = None
    mocker.patch('src.db.get_db_connection', return_value=conn)


class TestDownloadVideo:
    def test_download_success(self, mocker, tmp_path):
        """yt-dlp cria o arquivo esperado → download_video() retorna True."""
        _mock_pause_check(mocker)
        output_path = tmp_path / 'dQw4w9WgXcQ.mp4'
        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = lambda _urls: output_path.touch()

        mock_ydl_class = mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)

        # Disk space suficiente (10 GB livres)
        mocker.patch(
            'src.downloader.shutil.disk_usage',
            return_value=mocker.MagicMock(free=10 * 1024 * 1024 * 1024),
        )

        result = download_video('dQw4w9WgXcQ', str(output_path))

        assert result is True
        format_selector = mock_ydl_class.call_args.args[0]['format']
        assert 'height<=1080' in format_selector

    def test_download_without_output_file_returns_false(self, mocker, tmp_path):
        """yt-dlp sem erro, mas sem arquivo final, não pode ocupar a janela."""
        _mock_pause_check(mocker)
        output_path = tmp_path / 'dQw4w9WgXcQ.mp4'
        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.return_value = 0

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch(
            'src.downloader.shutil.disk_usage',
            return_value=mocker.MagicMock(free=10 * 1024 * 1024 * 1024),
        )

        result = download_video('dQw4w9WgXcQ', str(output_path))

        assert result is False

    def test_disk_space_guard(self, mocker, tmp_path):
        """shutil.disk_usage mockado com free=1GB (< 2GB mínimo)
        → download_video() retorna False sem chamar yt-dlp."""
        mocker.patch(
            'src.downloader.shutil.disk_usage',
            return_value=mocker.MagicMock(
                free=1 * 1024 * 1024 * 1024  # 1 GB < 2 GB mínimo
            ),
        )
        mock_ydl_class = mocker.patch('yt_dlp.YoutubeDL')

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        mock_ydl_class.assert_not_called()

    def test_partial_cleanup(self, mocker, tmp_path):
        """yt-dlp levanta DownloadError → arquivo .part é deletado via os.remove."""
        _mock_pause_check(mocker)
        import yt_dlp

        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError('network error')

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch(
            'src.downloader.shutil.disk_usage',
            return_value=mocker.MagicMock(free=10 * 1024 * 1024 * 1024),
        )

        # Criar arquivo .part fictício para simular download parcial
        part_file = tmp_path / 'dQw4w9WgXcQ.part'
        part_file.write_text('partial data')

        mock_remove = mocker.patch('src.downloader.os.remove')
        mocker.patch('src.downloader.glob.glob', return_value=[str(part_file)])
        mocker.patch('src.downloader.time.sleep')

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        mock_remove.assert_called_once_with(str(part_file))

    def test_permanent_error_no_retry(self, mocker, tmp_path):
        """DownloadError com mensagem 'private' → retorna False após 1 tentativa (não 3)."""
        _mock_pause_check(mocker)
        import yt_dlp

        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError('This video is private')

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch(
            'src.downloader.shutil.disk_usage',
            return_value=mocker.MagicMock(free=10 * 1024 * 1024 * 1024),
        )
        mocker.patch('src.downloader.glob.glob', return_value=[])

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        # Somente 1 tentativa para erros permanentes
        assert mock_ydl.download.call_count == 1

    def test_future_premiere_no_retry(self, mocker, tmp_path):
        """Estreia futura não deve bloquear a fila com três retries de 60s."""
        _mock_pause_check(mocker)
        import yt_dlp

        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError(
            'ERROR: [youtube] abc123: Premieres in 5 days'
        )

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch(
            'src.downloader.shutil.disk_usage',
            return_value=mocker.MagicMock(free=10 * 1024 * 1024 * 1024),
        )
        mocker.patch('src.downloader.glob.glob', return_value=[])

        result = download_video('abc123', str(tmp_path))

        assert result is False
        assert mock_ydl.download.call_count == 1

    def test_retry_transient_error(self, mocker, tmp_path):
        """DownloadError sem keyword permanente → tenta 3 vezes."""
        _mock_pause_check(mocker)
        import yt_dlp

        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError('connection reset')

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch(
            'src.downloader.shutil.disk_usage',
            return_value=mocker.MagicMock(free=10 * 1024 * 1024 * 1024),
        )
        mocker.patch('src.downloader.glob.glob', return_value=[])
        mocker.patch('src.downloader.time.sleep')

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        # 3 tentativas para erros transientes
        assert mock_ydl.download.call_count == 3


def _age(path, hours):
    """Envelhece o mtime do arquivo em `hours` horas."""
    old = time.time() - hours * 3600
    os.utime(path, (old, old))


class TestCleanupStaleDownloads:
    """Nomes reais tirados do disco de produção após crashes (Jul/Ago 2026)."""

    STALE_NAMES: ClassVar[list[str]] = [
        'QFDWHS3Oy3E.f298.mp4.part',
        'QFDWHS3Oy3E.f298.mp4.part-Frag923.part',
        'QFDWHS3Oy3E.f298.mp4.ytdl',
        'opkuWKRtSgM.f251.webm',
        'opkuWKRtSgM.f398.mp4',
        'opkuWKRtSgM.temp.mp4',
        'sgiB_gICFZQ.mp4.part',
    ]

    KEEP_NAMES: ClassVar[list[str]] = [
        '6hEpZ1ldzlg.mp4',  # raw completo — fila de download viva
        '-6CRTngWyDk_transcript.json',
        'A0n6KncVrMY_audio.mp3',
    ]

    def test_remove_todos_os_artefatos_de_trabalho(self, tmp_path):
        for name in self.STALE_NAMES:
            f = tmp_path / name
            f.write_text('x' * 10)
            _age(f, 12)

        result = cleanup_stale_downloads(max_age_hours=6, videos_dir=str(tmp_path))

        assert result['removed'] == len(self.STALE_NAMES)
        assert result['freed_bytes'] == 10 * len(self.STALE_NAMES)
        assert list(tmp_path.iterdir()) == []

    def test_preserva_arquivos_finais_mesmo_antigos(self, tmp_path):
        for name in self.KEEP_NAMES:
            f = tmp_path / name
            f.write_text('x')
            _age(f, 720)  # 30 dias

        result = cleanup_stale_downloads(max_age_hours=6, videos_dir=str(tmp_path))

        assert result['removed'] == 0
        assert sorted(p.name for p in tmp_path.iterdir()) == sorted(self.KEEP_NAMES)

    def test_preserva_download_em_andamento(self, tmp_path):
        """Artefato recente é download vivo — não pode ser apagado no meio."""
        recente = tmp_path / 'abc123.f299.mp4.part'
        recente.write_text('baixando')

        result = cleanup_stale_downloads(max_age_hours=6, videos_dir=str(tmp_path))

        assert result['removed'] == 0
        assert recente.exists()

    def test_ignora_subdiretorios(self, tmp_path):
        """clips/ e thumbnails/ têm outro ciclo de vida — cleanup não entra."""
        sub = tmp_path / 'clips'
        sub.mkdir()
        dentro = sub / 'orfao.mp4.part'
        dentro.write_text('x')
        _age(dentro, 48)

        result = cleanup_stale_downloads(max_age_hours=6, videos_dir=str(tmp_path))

        assert result['removed'] == 0
        assert dentro.exists()

    def test_diretorio_inexistente_nao_quebra(self, tmp_path):
        result = cleanup_stale_downloads(videos_dir=str(tmp_path / 'nao-existe'))

        assert result == {'removed': 0, 'freed_bytes': 0}
