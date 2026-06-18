"""
Testes ACQU-02: download 720p, disk guard, partial cleanup.

Módulo alvo: src.downloader
Exports esperados: download_video(video_id, output_path) -> bool

RED state: imports falham pois src/downloader.py ainda não existe.
"""
from src.downloader import download_video

MIN_FREE_SPACE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


class TestDownloadVideo:

    def test_download_success(self, mocker, tmp_path):
        """yt-dlp mockado sem erro → download_video() retorna True."""
        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.return_value = 0

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)

        # Disk space suficiente (10 GB livres)
        mocker.patch('src.downloader.shutil.disk_usage', return_value=mocker.MagicMock(
            free=10 * 1024 * 1024 * 1024
        ))

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is True

    def test_disk_space_guard(self, mocker, tmp_path):
        """shutil.disk_usage mockado com free=1GB (< 2GB mínimo)
        → download_video() retorna False sem chamar yt-dlp."""
        mock_disk = mocker.patch('src.downloader.shutil.disk_usage', return_value=mocker.MagicMock(
            free=1 * 1024 * 1024 * 1024  # 1 GB < 2 GB mínimo
        ))
        mock_ydl_class = mocker.patch('yt_dlp.YoutubeDL')

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        mock_ydl_class.assert_not_called()

    def test_partial_cleanup(self, mocker, tmp_path):
        """yt-dlp levanta DownloadError → arquivo .part é deletado via os.remove."""
        import yt_dlp

        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError('network error')

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch('src.downloader.shutil.disk_usage', return_value=mocker.MagicMock(
            free=10 * 1024 * 1024 * 1024
        ))

        # Criar arquivo .part fictício para simular download parcial
        part_file = tmp_path / 'dQw4w9WgXcQ.part'
        part_file.write_text('partial data')

        mock_remove = mocker.patch('src.downloader.os.remove')
        mocker.patch('src.downloader.glob.glob', return_value=[str(part_file)])

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        mock_remove.assert_called_once_with(str(part_file))

    def test_permanent_error_no_retry(self, mocker, tmp_path):
        """DownloadError com mensagem 'private' → retorna False após 1 tentativa (não 3)."""
        import yt_dlp

        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError('This video is private')

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch('src.downloader.shutil.disk_usage', return_value=mocker.MagicMock(
            free=10 * 1024 * 1024 * 1024
        ))
        mocker.patch('src.downloader.glob.glob', return_value=[])

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        # Somente 1 tentativa para erros permanentes
        assert mock_ydl.download.call_count == 1

    def test_retry_transient_error(self, mocker, tmp_path):
        """DownloadError sem keyword permanente → tenta 3 vezes."""
        import yt_dlp

        mock_ydl = mocker.MagicMock()
        mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
        mock_ydl.download.side_effect = yt_dlp.utils.DownloadError('connection reset')

        mocker.patch('yt_dlp.YoutubeDL', return_value=mock_ydl)
        mocker.patch('src.downloader.shutil.disk_usage', return_value=mocker.MagicMock(
            free=10 * 1024 * 1024 * 1024
        ))
        mocker.patch('src.downloader.glob.glob', return_value=[])

        result = download_video('dQw4w9WgXcQ', str(tmp_path))

        assert result is False
        # 3 tentativas para erros transientes
        assert mock_ydl.download.call_count == 3
