#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Uso: CONFIRM_RESTORE=I_UNDERSTAND $0 /caminho/backup.sql.gz" >&2
    exit 2
fi

BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Backup não encontrado: $BACKUP_FILE" >&2
    exit 1
fi

BACKUP_FILE="$(cd -- "$(dirname -- "$BACKUP_FILE")" && pwd)/$(basename -- "$BACKUP_FILE")"

if [[ "${CONFIRM_RESTORE:-}" != "I_UNDERSTAND" ]]; then
    echo "Restauração sobrescreve dados existentes. Defina CONFIRM_RESTORE=I_UNDERSTAND para continuar." >&2
    exit 2
fi

gzip -t "$BACKUP_FILE"
if [[ -f "${BACKUP_FILE}.sha256" ]]; then
    (cd -- "$(dirname -- "$BACKUP_FILE")" && sha256sum -c "$(basename -- "${BACKUP_FILE}.sha256")")
fi

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

docker compose exec -T mysql sh -c 'mysqladmin --protocol=TCP -uroot -p"$MYSQL_ROOT_PASSWORD" ping --silent'
gzip -dc "$BACKUP_FILE" | docker compose exec -T mysql sh -c 'mysql --protocol=TCP -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'
