#!/usr/bin/env python3
"""
Gera token OAuth por canal-destino (multi-canal Phase 7).
Salva em token-{slug}.json no mesmo diretório.

Uso:
    cd /Users/alessandrobm1/develop/server/wordpress/canaldecortes/youtube
    python generate_token_channel.py --channel futebol-em-cortes
"""

import argparse
import json
import os
import sys

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERRO: Dependências não instaladas.")
    print("Executar: pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")


def main():
    parser = argparse.ArgumentParser(description="Gera token OAuth por canal-destino")
    parser.add_argument("--channel", required=True, help="Slug do canal (ex: futebol-em-cortes)")
    args = parser.parse_args()

    token_file = os.path.join(SCRIPT_DIR, f"token-{args.channel}.json")

    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"ERRO: client_secret.json não encontrado em {CLIENT_SECRET_FILE}")
        sys.exit(1)

    print(f"Gerando token para canal: {args.channel}")
    print("Um browser será aberto. Faça login com a conta do canal e autorize.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    creds_data = json.loads(creds.to_json())
    if not creds_data.get("refresh_token"):
        print("AVISO: refresh_token não obtido. Revogue o acesso em:")
        print("  https://myaccount.google.com/permissions")
        print("e execute novamente.")
        sys.exit(1)

    with open(token_file, "w") as f:
        json.dump(creds_data, f, indent=2)

    print(f"Token salvo em: {token_file}")
    print("refresh_token: presente")


if __name__ == "__main__":
    main()
