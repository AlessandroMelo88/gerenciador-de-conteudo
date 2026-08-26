#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

PGHOST="${PGHOST:-postgres}"
PGDATABASE="${PGDATABASE:-clips_automation}"
PGUSER="${PGUSER:-clips_user}"
PGPASSWORD="${PGPASSWORD:?PGPASSWORD is required}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_INTERVAL_SECONDS="${BACKUP_INTERVAL_SECONDS:-86400}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

export PGPASSWORD
mkdir -p "$BACKUP_DIR"

backup_once() {
    local timestamp backup_file checksum_file temporary_file
    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    backup_file="$BACKUP_DIR/${PGDATABASE}_${timestamp}.sql.gz"
    checksum_file="${backup_file}.sha256"
    temporary_file="${backup_file}.tmp.$$"

    echo "[postgres-backup] aguardando PostgreSQL em ${PGHOST}"
    pg_isready --host="$PGHOST" --username="$PGUSER" --dbname="$PGDATABASE" --timeout=10

    echo "[postgres-backup] criando ${backup_file}"
    if pg_dump \
        --host="$PGHOST" \
        --username="$PGUSER" \
        --dbname="$PGDATABASE" \
        --no-owner \
        --no-privileges \
        --format=plain | gzip -c > "$temporary_file"; then
        mv "$temporary_file" "$backup_file"
        chmod 600 "$backup_file"
        (
            cd -- "$BACKUP_DIR"
            sha256sum "$(basename -- "$backup_file")" > "$(basename -- "$checksum_file")"
        )
        chmod 600 "$checksum_file"
        echo "[postgres-backup] concluído: ${backup_file}"
    else
        rm -f "$temporary_file"
        echo "[postgres-backup] falha ao gerar ${backup_file}" >&2
        return 1
    fi

    find "$BACKUP_DIR" -type f \
        \( -name "${PGDATABASE}_*.sql.gz" -o -name "${PGDATABASE}_*.sql.gz.sha256" \) \
        -mtime +"$BACKUP_RETENTION_DAYS" \
        -delete
}

if [[ "${BACKUP_ONCE:-false}" == "true" ]]; then
    backup_once
    exit 0
fi

while true; do
    if backup_once; then
        sleep "$BACKUP_INTERVAL_SECONDS"
    else
        sleep 300
    fi
done
