#!/usr/bin/env bash
# Funções compartilhadas pelos comandos de operação manual do pipeline.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname -- "$SCRIPT_DIR")"

if [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT_DIR/.env"
  set +a
fi

POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-clips_user}"
POSTGRES_DB="${POSTGRES_DB:-clips_automation}"
POSTGRES_PASSWORD="${CLIPS_DB_PASSWORD:-${POSTGRES_PASSWORD:-}}"

postgres_exec() {
  local sql="$1"
  docker compose exec -T \
    -e "PGPASSWORD=$POSTGRES_PASSWORD" \
    "$POSTGRES_SERVICE" \
    psql --set=ON_ERROR_STOP=1 \
      --username="$POSTGRES_USER" \
      --dbname="$POSTGRES_DB" \
      --tuples-only --no-align --quiet \
      --command="$sql"
}

postgres_exec_pretty() {
  local sql="$1"
  docker compose exec -T \
    -e "PGPASSWORD=$POSTGRES_PASSWORD" \
    "$POSTGRES_SERVICE" \
    psql --set=ON_ERROR_STOP=1 \
      --username="$POSTGRES_USER" \
      --dbname="$POSTGRES_DB" \
      --pset=pager=off \
      --command="$sql"
}

postgres_exec_expanded() {
  local sql="$1"
  docker compose exec -T \
    -e "PGPASSWORD=$POSTGRES_PASSWORD" \
    "$POSTGRES_SERVICE" \
    psql --set=ON_ERROR_STOP=1 \
      --username="$POSTGRES_USER" \
      --dbname="$POSTGRES_DB" \
      --expanded --pset=pager=off \
      --command="$sql"
}

postgres_exec_vars() {
  local sql="$1"
  shift
  docker compose exec -T \
    -e "PGPASSWORD=$POSTGRES_PASSWORD" \
    "$POSTGRES_SERVICE" \
    psql --set=ON_ERROR_STOP=1 \
      --username="$POSTGRES_USER" \
      --dbname="$POSTGRES_DB" \
      --tuples-only --no-align --quiet \
      "$@" \
      --command="$sql"
}
