#!/usr/bin/env python3
"""
Canal de Cortes — Geração de token OAuth do YouTube
Executar UMA VEZ para autorizar o acesso ao canal do YouTube.

Pré-requisitos:
1. client_secret.json no mesmo diretório (baixado do Google Cloud Console)
2. pip install google-auth-oauthlib google-api-python-client

Uso:
    cd /Users/alessandrobm1/develop/server/wordpress/canaldecortes/youtube
    python generate_token.py
"""

import json
import os
import sys

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Verificar dependências antes de importar
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
except ImportError:
    print("ERRO: Dependências não instaladas.")
    print("Executar: pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")


def main():
    # Verificar client_secret.json
    if not os.path.exists(CLIENT_SECRET_FILE):
        print("ERRO: client_secret.json não encontrado.")
        print(f"Esperado em: {CLIENT_SECRET_FILE}")
        print()
        print("Para obter o arquivo:")
        print("  1. https://console.cloud.google.com/")
        print("  2. APIs & Services → Credentials")
        print("  3. Create Credentials → OAuth client ID → Desktop app")
        print("  4. Download JSON → renomear para client_secret.json")
        sys.exit(1)

    print("Iniciando autorização OAuth do YouTube...")
    print("Um browser será aberto. Faça login com a conta do canal e autorize o acesso.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
    )

    # access_type=offline + prompt=consent garante refresh_token permanente
    # Sem isso, o token expira em 1h e não há como renovar automaticamente
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    # Verificar que refresh_token foi obtido
    creds_data = json.loads(creds.to_json())
    if not creds_data.get("refresh_token"):
        print()
        print("AVISO: refresh_token não obtido.")
        print("Isso pode acontecer se você já autorizou antes sem revogar.")
        print("Para resolver: https://myaccount.google.com/permissions → revogar acesso → rodar novamente")
        sys.exit(1)

    # Salvar token
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print()
    print(f"token.json salvo em: {TOKEN_FILE}")
    print(f"refresh_token: {'presente' if creds_data.get('refresh_token') else 'AUSENTE'}")
    print()
    print("IMPORTANTE: NÃO commitar token.json no git (já está no .gitignore)")
    print()
    print("Próximo passo:")
    print("  Mudar app para modo Production no Google Cloud Console para evitar")
    print("  expiração do token em 7 dias:")
    print("  APIs & Services → OAuth consent screen → Publish App")


if __name__ == "__main__":
    main()
