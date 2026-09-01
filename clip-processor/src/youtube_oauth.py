"""
Helper CLI para gerar token OAuth YouTube por canal-destino.

Uso:
    python -m src.youtube_oauth --channel <slug>
    python src/youtube_oauth.py --channel <slug>

Exemplos:
    python -m src.youtube_oauth --channel futebol-em-cortes
    python -m src.youtube_oauth --channel podcast-cortes

O token é salvo em /app/youtube/token-{slug}.json.
O arquivo client_secrets.json é lido de YOUTUBE_CLIENT_SECRETS (env var).
Default: /app/youtube/client_secrets.json

Para canais adicionais, copie o client_secrets do GCP Project correspondente:
    cp client_secrets-podcast-cortes.json /app/youtube/client_secrets-podcast-cortes.json
    YOUTUBE_CLIENT_SECRETS=/app/youtube/client_secrets-podcast-cortes.json \\
        python -m src.youtube_oauth --channel podcast-cortes

IMPORTANTE:
    - Cada canal-destino deve ter seu proprio GCP Project (cota separada de 10.000 units/dia).
    - Token gerado em modo Testing expira em 7 dias — publicar app em Production no GCP Console.
    - Nao commitar token-*.json no git (ja no .gitignore).
"""

import argparse
import json
import os
from pathlib import Path

# Permite redirecionamento OAuth em http://localhost
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SECRETS_FILE = os.environ.get(
    "YOUTUBE_CLIENT_SECRETS", "/app/youtube/client_secrets.json"
)


def generate_token(channel_slug: str, secrets_file: str = None) -> str:
    """Gera token OAuth para o canal-destino e salva em /app/youtube/token-{slug}.json.

    Args:
        channel_slug: Slug do canal destino (ex: futebol-em-cortes).
        secrets_file: Caminho para client_secrets.json. Default: SECRETS_FILE global.

    Returns:
        Caminho do arquivo token salvo.
    """
    if secrets_file is None:
        secrets_file = SECRETS_FILE

    token_path = f"/app/youtube/token-{channel_slug}.json"

    if not os.path.exists(secrets_file):
        raise FileNotFoundError(
            f"client_secrets.json nao encontrado em: {secrets_file}\n"
            "Defina YOUTUBE_CLIENT_SECRETS ou copie o arquivo para o caminho default."
        )

    flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
    flow.redirect_uri = "http://localhost:8085/"
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

    print(f"\nAbra esta URL no browser:\n\n{auth_url}\n")
    print("Depois de autorizar, o browser vai tentar abrir localhost:8085 e mostrar erro.")
    print("Isso e normal. Copie a URL COMPLETA da barra do browser e cole aqui:")
    redirect_response = input("> ").strip()
    if redirect_response.startswith("http://"):
        redirect_response = "https://" + redirect_response[7:]

    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials

    creds_data = json.loads(creds.to_json())
    if not creds_data.get("refresh_token"):
        raise RuntimeError(
            "refresh_token nao obtido. Revogue o acesso em:\n"
            "  https://myaccount.google.com/permissions\n"
            "e execute novamente."
        )

    Path(token_path).parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        json.dump(creds_data, f, indent=2)

    return token_path


def main():
    parser = argparse.ArgumentParser(
        description="Gera token OAuth YouTube por canal-destino"
    )
    parser.add_argument(
        "--channel",
        required=True,
        help="Slug do canal destino (ex: futebol-em-cortes, podcast-cortes)",
    )
    args = parser.parse_args()

    print(f"Gerando token OAuth para canal: {args.channel}")
    print(f"Usando client_secrets: {SECRETS_FILE}")
    print()

    token_path = generate_token(args.channel)
    print(f"Token salvo em: {token_path}")
    print()
    print("IMPORTANTE: Publicar app em Production no GCP Console para evitar expiracao em 7 dias.")
    print("  APIs & Services -> OAuth consent screen -> Publish App")


if __name__ == "__main__":
    main()
