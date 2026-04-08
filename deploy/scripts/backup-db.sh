#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE=${COMPOSE:-docker-compose}
PROJECT=${INSTANCE_PROJECT:-inst-xiaocai-dev}
DB_NAME=${POSTGRES_DB:-xiaocai}
DB_USER=${POSTGRES_USER:-xiaocai}
OUT_DIR=${BACKUP_DIR:-./backups}
TS=$(date +%Y%m%d-%H%M%S)
OUT_FILE="$OUT_DIR/postgres-${DB_NAME}-${TS}.sql"

mkdir -p "$OUT_DIR"

echo "creating backup: $OUT_FILE"
$COMPOSE -p "$PROJECT" -f compose.instance.yml exec -T inst-xiaocai-postgres \
  pg_dump -U "$DB_USER" "$DB_NAME" > "$OUT_FILE"

echo "backup complete: $OUT_FILE"
