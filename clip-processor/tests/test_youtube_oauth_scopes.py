"""O token precisa nascer com o escopo de leitura do Analytics (SPEC-001 R5)."""
from src import youtube_oauth


def test_scopes_incluem_analytics_readonly():
    assert 'https://www.googleapis.com/auth/yt-analytics.readonly' in youtube_oauth.SCOPES


def test_scopes_de_upload_continuam():
    # Tirar um escopo existente invalidaria o token para publicar.
    assert 'https://www.googleapis.com/auth/youtube.upload' in youtube_oauth.SCOPES
    assert 'https://www.googleapis.com/auth/youtube.force-ssl' in youtube_oauth.SCOPES
