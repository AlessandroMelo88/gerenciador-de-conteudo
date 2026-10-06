#!/usr/bin/env python3
"""
Gera token OAuth por canal-destino (multi-canal Phase 7).
Salva em token-{slug}.json no mesmo diretório.

Depois do consentimento, CONFERE em qual canal do YouTube o token caiu e aborta
se não for o canal esperado — foi assim que, em 02/10/2026, o token de
futebol-em-cortes passou a apontar para o canal pessoal "Alessandro Melo" e
quatro dias de clips subiram privados no lugar errado.

Uso:
    cd /Users/alessandrobm1/develop/server/wordpress/canaldecortes
    .venv/bin/python youtube/generate_token_channel.py --channel futebol-em-cortes

O canal esperado vem de EXPECTED_CHANNEL_IDS (abaixo) ou de --expect-channel-id.
Pular a conferência: --skip-verify (não use sem motivo).
"""

import argparse
import json
import os
import sys

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("ERRO: Dependências não instaladas.")
    print("Executar: .venv/bin/pip install google-auth-oauthlib google-api-python-client")
    sys.exit(1)

# force-ssl é necessário para channels.list(mine=True), que confere a identidade
# do token logo após o consentimento.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# Espelha destination_channels.youtube_channel_id em produção.
EXPECTED_CHANNEL_IDS = {
    "futebol-em-cortes": "UCcyeBQFAkUNeDJbBM7JJqLw",
    "fatos-e-debates": "UCCx9rlpbNdfLBTLqGah78cA",
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")


def verify_channel(creds, expected_id: str) -> None:
    """Aborta se o token não for do canal esperado."""
    youtube = build("youtube", "v3", credentials=creds)
    items = youtube.channels().list(part="snippet", mine=True).execute().get("items", [])
    if not items:
        print("ERRO: o token não devolveu nenhum canal. Refaça escolhendo o canal certo.")
        sys.exit(1)

    got_id = items[0]["id"]
    got_title = items[0]["snippet"]["title"]
    if got_id != expected_id:
        print()
        print("ERRO: token gerado para o CANAL ERRADO — nada foi salvo.")
        print(f"  esperado: {expected_id}")
        print(f"  obtido:   {got_id} ({got_title})")
        print()
        print("Na tela do Google, escolha a CONTA DE MARCA do canal destino,")
        print("não a conta pessoal. Rode de novo.")
        sys.exit(1)

    print(f"Canal conferido: {got_title} ({got_id})")


def main():
    parser = argparse.ArgumentParser(description="Gera token OAuth por canal-destino")
    parser.add_argument("--channel", required=True, help="Slug do canal (ex: futebol-em-cortes)")
    parser.add_argument("--expect-channel-id", help="ID do canal YouTube esperado (sobrescreve a tabela interna)")
    parser.add_argument("--skip-verify", action="store_true", help="Não conferir o canal (desaconselhado)")
    args = parser.parse_args()

    token_file = os.path.join(SCRIPT_DIR, f"token-{args.channel}.json")
    expected_id = args.expect_channel_id or EXPECTED_CHANNEL_IDS.get(args.channel)

    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"ERRO: client_secret.json não encontrado em {CLIENT_SECRET_FILE}")
        sys.exit(1)

    if not expected_id and not args.skip_verify:
        print(f"ERRO: canal '{args.channel}' não está em EXPECTED_CHANNEL_IDS.")
        print("Passe --expect-channel-id <ID> ou --skip-verify.")
        sys.exit(1)

    print(f"Gerando token para canal: {args.channel}")
    if expected_id:
        print(f"Canal esperado: {expected_id}")
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

    if not args.skip_verify:
        verify_channel(creds, expected_id)

    with open(token_file, "w") as f:
        json.dump(creds_data, f, indent=2)

    print(f"Token salvo em: {token_file}")
    print("refresh_token: presente")
    print()
    print("Enviar para produção:")
    print(f"  scp -i ~/.ssh/oracle-a1-2026-09-16.key {token_file} \\")
    print("      ubuntu@129.80.236.185:/home/ubuntu/canaldecortes/youtube/")


if __name__ == "__main__":
    main()
