#!/usr/bin/env bash
# Postgres de desenvolvimento COM pgvector, num container avulso do Canal de Cortes.
#
# Não toca no Postgres compartilhado do ../docker-compose.yml (porta 5432, kelnab e
# outros), que não tem a extensão. Este sobe na porta 5433 com a mesma imagem que
# vai para produção (docker/postgres/Dockerfile).
#
# Uso:
#   scripts/dev-pgvector.sh            # constrói a imagem (se faltar) e sobe
#   scripts/dev-pgvector.sh status     # mostra o estado e as extensões
#   scripts/dev-pgvector.sh stop       # para o container (o volume fica)
#   scripts/dev-pgvector.sh destroy    # remove container E volume deste script
#
# Depois, no painel/.env:  DB_HOST=127.0.0.1  DB_PORT=5433
# e rode:  cd painel && php artisan migrate
# Testes: DB_HOST=127.0.0.1 DB_PORT=5433 php artisan test  (o phpunit.xml aceita override)
set -euo pipefail

NAME="${PGVECTOR_DEV_NAME:-canaldecortes-pgvector}"
PORT="${PGVECTOR_DEV_PORT:-5433}"
VOLUME="${NAME}_data"
IMAGE="canaldecortes-postgres:pg17-vector"
DB="${POSTGRES_DB:-clips_automation}"
USER_="${POSTGRES_USER:-clips_user}"
PASS="${POSTGRES_PASSWORD:-clips_local_dev}"   # só dev local; nunca usar em produção

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cmd="${1:-up}"

case "$cmd" in
  up)
    if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
      docker build -t "$IMAGE" "$ROOT/docker/postgres"
    fi
    if docker ps -a --format '{{.Names}}' | grep -qx "$NAME"; then
      docker start "$NAME" >/dev/null
    else
      docker run -d --name "$NAME" --restart unless-stopped \
        -p "127.0.0.1:${PORT}:5432" \
        -e POSTGRES_DB="$DB" -e POSTGRES_USER="$USER_" -e POSTGRES_PASSWORD="$PASS" \
        -v "${VOLUME}:/var/lib/postgresql/data" \
        "$IMAGE" -c maintenance_work_mem=256MB >/dev/null
    fi
    echo "Aguardando o Postgres..."
    for _ in $(seq 1 30); do
      docker exec "$NAME" pg_isready -U "$USER_" -d "$DB" >/dev/null 2>&1 && break
      sleep 1
    done
    echo "Pronto: 127.0.0.1:${PORT} (banco ${DB}, usuário ${USER_})"
    ;;
  status)
    docker ps -a --filter "name=^${NAME}$" --format 'container: {{.Names}} | {{.Status}} | {{.Ports}}'
    docker exec "$NAME" psql -U "$USER_" -d "$DB" -c \
      "SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name IN ('vector','pg_trgm','unaccent')"
    ;;
  stop)
    docker stop "$NAME"
    ;;
  destroy)
    # Só o que este script criou (nome e volume próprios).
    docker rm -f "$NAME"
    docker volume rm "$VOLUME"
    ;;
  *)
    echo "uso: $0 [up|status|stop|destroy]" >&2
    exit 2
    ;;
esac
