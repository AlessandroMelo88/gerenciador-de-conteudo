#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
VENV="$ROOT/clip-processor/.venv"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3 não encontrado. Instale Python 3.11+ e execute novamente." >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
    echo "Instale ffmpeg e ffprobe antes de configurar os workers." >&2
    echo "macOS: brew install ffmpeg" >&2
    echo "Debian/Ubuntu: sudo apt-get install ffmpeg" >&2
    exit 1
fi

"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' || {
    echo "Python 3.11 ou superior é necessário." >&2
    exit 1
}

if [[ ! -f "$ROOT/.env" ]]; then
    cp "$ROOT/.env.native.example" "$ROOT/.env"
    chmod 600 "$ROOT/.env"
    echo "Criei .env a partir de .env.native.example; preencha banco, Redis, Groq e OAuth."
else
    echo "Mantive o .env existente. O runner converte caminhos /app padrão para pastas locais."
fi

"$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install -r "$ROOT/clip-processor/requirements.txt"
mkdir -p "$ROOT/var/videos" "$ROOT/var/native-worker/locks" "$ROOT/var/native-worker/logs"

echo "Ambiente nativo preparado. Revise .env e habilite PIPELINE_ENABLED=true quando estiver pronto."
echo "Depois instale os agendamentos com: $VENV/bin/python $ROOT/scripts/install_native_cron.py"
