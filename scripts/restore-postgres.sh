#!/usr/bin/env bash
# Restaura um backup do PostgreSQL no container `postgres` (o mesmo nome da produção na A1
# e do compose do projeto). SOBRESCREVE dados: exige CONFIRM_RESTORE=I_UNDERSTAND.
#
# Formatos aceitos:
#   *.sql.gz  dump SQL em texto, comprimido  -> psql
#   *.dump    formato custom do pg_dump -Fc  -> pg_restore --clean --if-exists
# Se existir <arquivo>.sha256 ao lado, o checksum é conferido antes.
#
# Uso:
#   CONFIRM_RESTORE=I_UNDERSTAND scripts/restore-postgres.sh /caminho/backup.sql.gz
#   POSTGRES_CONTAINER=outro-nome ...   # se o container não se chamar `postgres`
#
# Antes de restaurar em produção: tire um dump novo do estado atual (runbook em
# Docs/operacao/RUNBOOK.md) e pause o clip-processor. Nunca `docker compose down -v`.
set -Eeuo pipefail

CONTAINER="${POSTGRES_CONTAINER:-postgres}"

if [[ $# -ne 1 ]]; then
    echo "Uso: CONFIRM_RESTORE=I_UNDERSTAND $0 /caminho/backup.sql.gz|backup.dump" >&2
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

if [[ -f "${BACKUP_FILE}.sha256" ]]; then
    (
        cd -- "$(dirname -- "$BACKUP_FILE")"
        if command -v sha256sum >/dev/null 2>&1; then
            sha256sum -c "$(basename -- "${BACKUP_FILE}.sha256")"
        else
            shasum -a 256 -c "$(basename -- "${BACKUP_FILE}.sha256")"
        fi
    )
fi

docker exec "$CONTAINER" sh -c \
    'pg_isready --host=127.0.0.1 --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"'

case "$BACKUP_FILE" in
    *.sql.gz)
        gzip -t "$BACKUP_FILE"
        gzip -dc "$BACKUP_FILE" | docker exec -i "$CONTAINER" sh -c \
            'psql --set ON_ERROR_STOP=1 --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"'
        ;;
    *.dump)
        docker exec -i "$CONTAINER" sh -c \
            'pg_restore --clean --if-exists --no-owner --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
            < "$BACKUP_FILE"
        ;;
    *)
        echo "Extensão não reconhecida (use .sql.gz ou .dump): $BACKUP_FILE" >&2
        exit 2
        ;;
esac

echo "Restauração concluída a partir de $BACKUP_FILE"
