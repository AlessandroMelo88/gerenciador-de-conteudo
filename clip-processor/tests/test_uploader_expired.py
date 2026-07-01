"""RED test para captura de RefreshError e persistência de oauth_expired_flag
(implementação GREEN no Plan 08-06)."""
import pytest
from unittest.mock import patch, MagicMock

from src.uploader import YouTubeUploader


def test_load_credentials_catches_refresh_error_and_flags_channel(tmp_path):
    """RefreshError em creds.refresh() deve setar oauth_expired_flag=TRUE em
    destination_channels para o channel_slug atual."""
    try:
        from google.auth.exceptions import RefreshError
    except ModuleNotFoundError:
        RefreshError = type('RefreshError', (Exception,), {})

    token_file = tmp_path / 'token-futebol-em-cortes.json'
    token_file.write_text('{}')

    uploader = YouTubeUploader(channel_slug='futebol-em-cortes')
    # Force the token_file to the tmp path
    uploader.token_file = str(token_file)

    fake_creds = MagicMock()
    fake_creds.expired = True
    fake_creds.refresh_token = 'stale'
    fake_creds.refresh.side_effect = RefreshError('invalid_grant: Token has been expired or revoked')

    fake_conn = MagicMock()
    fake_cursor = MagicMock()
    fake_conn.cursor.return_value.__enter__.return_value = fake_cursor

    with patch('src.uploader.Credentials.from_authorized_user_file', return_value=fake_creds), \
         patch('src.uploader.db_connect', return_value=fake_conn):
        with pytest.raises(RefreshError):
            uploader._load_credentials()

    # Assert: uploader marcou a coluna oauth_expired_flag=TRUE para este slug.
    calls = [c.args[0] for c in fake_cursor.execute.call_args_list]
    assert any('oauth_expired_flag' in sql and 'destination_channels' in sql for sql in calls), (
        f'Nenhum UPDATE em destination_channels.oauth_expired_flag detectado. SQLs vistas: {calls}'
    )
