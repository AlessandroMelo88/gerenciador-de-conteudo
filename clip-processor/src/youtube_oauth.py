"""
youtube_oauth.py — Helper para geracao de token OAuth YouTube por canal-destino (OAU-01).

Implementado em Plan 06-01.

Gera credenciais OAuth com offline access (refresh_token) para cada canal-destino
e salva em /app/youtube/token-{slug}.json.

Uso CLI interativo:
    docker exec -it clip-processor python -m src.youtube_oauth --channel canal-slug

Fluxo:
    1. Lê /app/youtube/client_secrets.json (ou YOUTUBE_CLIENT_SECRETS)
    2. Imprime auth URL com prompt=consent e access_type=offline
    3. Aguarda usuario autorizar e colar a URL de redirect (localhost:8085/?code=...)
    4. Valida que refresh_token está presente no token obtido
    5. Salva em /app/youtube/token-{channel_slug}.json com permissões 600

Exporta:
    - generate_token(channel_slug, secrets_file=None) -> str
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.paths import YOUTUBE_CLIENT_SECRETS, YOUTUBE_DIR

# Permite redirecionamento OAuth em http://localhost
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
]
SECRETS_FILE = YOUTUBE_CLIENT_SECRETS


def generate_token(channel_slug: str, secrets_file: str | None = None) -> str:
    """Gera token OAuth para o canal-destino e salva em /app/youtube/token-{slug}.json.

    Args:
        channel_slug: slug do canal destino (ex: 'futebol-em-cortes')
        secrets_file: caminho alternativo para client_secrets.json (default: SECRETS_FILE)

    Returns:
        str: caminho do arquivo de token salvo

    Raises:
        FileNotFoundError: se client_secrets.json não existir
        RuntimeError: se refresh_token não vier nas credenciais obtidas
    """
    if secrets_file is None:
        secrets_file = SECRETS_FILE

    token_path = os.path.join(YOUTUBE_DIR, f'token-{channel_slug}.json')

    if not os.path.exists(secrets_file):
        raise FileNotFoundError(
            f'client_secrets.json nao encontrado em: {secrets_file}\n'
            'Defina YOUTUBE_CLIENT_SECRETS ou copie o arquivo para o caminho default.'
        )

    flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
    flow.redirect_uri = 'http://localhost:8085/'
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')

    print(f'\nAbra esta URL no browser:\n\n{auth_url}\n')
    print('Depois de autorizar, o browser vai tentar abrir localhost:8085 e mostrar erro.')
    print('Isso e normal. Copie a URL COMPLETA da barra do browser e cole aqui:')
    redirect_response = input('> ').strip()
    if redirect_response.startswith('http://'):
        redirect_response = 'https://' + redirect_response[7:]

    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials

    creds_data = json.loads(creds.to_json())
    if not creds_data.get('refresh_token'):
        raise RuntimeError(
            'refresh_token nao obtido. Revogue o acesso em:\n'
            '  https://myaccount.google.com/permissions\n'
            'e execute novamente.'
        )

    Path(token_path).parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, 'w') as f:
        json.dump(creds_data, f, indent=2)

    return token_path


def main():
    parser = argparse.ArgumentParser(description='Gera token OAuth YouTube por canal-destino')
    parser.add_argument(
        '--channel',
        required=True,
        help='Slug do canal destino (ex: futebol-em-cortes, podcast-cortes)',
    )
    args = parser.parse_args()

    print(f'Gerando token OAuth para canal: {args.channel}')
    print(f'Usando client_secrets: {SECRETS_FILE}')
    print()

    token_path = generate_token(args.channel)
    print(f'Token salvo em: {token_path}')
    print()
    print('IMPORTANTE: Publicar app em Production no GCP Console para evitar expiracao em 7 dias.')
    print('  APIs & Services -> OAuth consent screen -> Publish App')


if __name__ == '__main__':
    main()
