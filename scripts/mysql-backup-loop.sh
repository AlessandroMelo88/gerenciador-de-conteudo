#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_DATABASE="${MYSQL_DATABASE:-clips_automation}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?MYSQL_PASSWORD is required}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_INTERVAL_SECONDS="${BACKUP_INTERVAL_SECONDS:-86400}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

backup_once() {
    local timestamp backup_file checksum_file temporary_file
    timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
    backup_file="$BACKUP_DIR/${MYSQL_DATABASE}_${timestamp}.sql.gz"
    checksum_file="${backup_file}.sha256"
    temporary_file="${backup_file}.tmp.$$"

    echo "[mysql-backup] aguardando MySQL em ${MYSQL_HOST}"
    mysqladmin \
        --protocol=TCP \
        --host="$MYSQL_HOST" \
        --user="$MYSQL_USER" \
        --password="$MYSQL_PASSWORD" \
        ping --silent

    echo "[mysql-backup] criando ${backup_file}"
    if mysqldump \
        --protocol=TCP \
        --host="$MYSQL_HOST" \
        --user="$MYSQL_USER" \
        --password="$MYSQL_PASSWORD" \
        --single-transaction \
        --skip-lock-tables \
        --quick \
        --routines \
        --events \
        --triggers \
        --hex-blob \
        "$MYSQL_DATABASE" | gzip -c > "$temporary_file"; then
        mv "$temporary_file" "$backup_file"
        chmod 600 "$backup_file"
        (
            cd -- "$BACKUP_DIR"
            sha256sum "$(basename -- "$backup_file")" > "$(basename -- "$checksum_file")"
        )
        chmod 600 "$checksum_file"
        echo "[mysql-backup] concluído: ${backup_file}"
    else
        rm -f "$temporary_file"
        echo "[mysql-backup] falha ao gerar ${backup_file}" >&2
        return 1
    fi

    find "$BACKUP_DIR" -type f \
        \( -name "${MYSQL_DATABASE}_*.sql.gz" -o -name "${MYSQL_DATABASE}_*.sql.gz.sha256" \) \
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
