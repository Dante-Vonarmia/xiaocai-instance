#!/usr/bin/env bash

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <backup.sql>"
  exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "backup file not found: $BACKUP_FILE"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE=${COMPOSE:-docker-compose}
PROJECT=${INSTANCE_PROJECT:-inst-xiaocai-dev}
DB_NAME=${POSTGRES_DB:-xiaocai}
DB_USER=${POSTGRES_USER:-xiaocai}

echo "restoring from: $BACKUP_FILE"
cat "$BACKUP_FILE" | $COMPOSE -p "$PROJECT" -f compose.instance.yml exec -T inst-xiaocai-postgres \
  psql -U "$DB_USER" "$DB_NAME"

echo "restore complete"
