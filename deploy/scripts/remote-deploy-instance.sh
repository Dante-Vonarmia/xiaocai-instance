#!/usr/bin/env bash
set -euo pipefail

# 在服务器上执行 instance 部署（仅 instance，不启 devlib）
# 用法:
#   REPO_DIR=/opt/xiaocai-instance ./deploy/scripts/remote-deploy-instance.sh

REPO_DIR=${REPO_DIR:-$HOME/mnt/xiaocai-instance}
DEPLOY_DIR="$REPO_DIR/deploy"
SKIP_API_SMOKE=${SKIP_API_SMOKE:-false}
FRONTEND_DEPLOY_MODE=${FRONTEND_DEPLOY_MODE:-standalone}

if [ ! -d "$DEPLOY_DIR" ]; then
  echo "deploy dir not found: $DEPLOY_DIR"
  exit 1
fi

cd "$DEPLOY_DIR"

if [ ! -f .env ]; then
  echo ".env not found in $DEPLOY_DIR"
  echo "hint: copy .env.production or .env.production.example to .env first"
  exit 1
fi

require_non_empty() {
  local key="$1"
  local value
  value=$(grep -E "^${key}=" .env | head -n1 | cut -d'=' -f2- || true)
  if [ -z "${value}" ]; then
    echo "required env missing or empty: ${key}"
    exit 1
  fi
}

require_non_empty INSTANCE_JWT_SECRET
require_non_empty ROOT_AUTH_TOKEN
require_non_empty STORAGE_DB_URL

reject_placeholder() {
  local key="$1"
  local value
  value=$(grep -E "^${key}=" .env | head -n1 | cut -d'=' -f2- || true)
  if [[ "$value" == *replace-with* ]] || [[ "$value" == *your-kernel-host* ]]; then
    echo "env contains placeholder value, please set real value: ${key}"
    exit 1
  fi
}

reject_placeholder INSTANCE_JWT_SECRET
reject_placeholder ROOT_AUTH_TOKEN
reject_placeholder STORAGE_DB_URL
reject_placeholder KERNEL_BASE_URL

if ! grep -Eq '^ENABLE_DEVLIB_FLARE=false$' .env; then
  echo "ENABLE_DEVLIB_FLARE must be false for production deploy"
  exit 1
fi

if ! grep -Eq '^MOCK_AUTH=false$' .env; then
  echo "MOCK_AUTH must be false for production deploy"
  exit 1
fi

echo "[deploy] config check"
make config-instance

echo "[deploy] attempt backup before cutover (skip on first deployment)"
if ! make backup-db; then
  echo "[deploy] backup skipped (no running stack or first deployment)"
fi

echo "[deploy] stop old instance stack"
make down-instance || true

if [ "$FRONTEND_DEPLOY_MODE" = "standalone" ]; then
  echo "[deploy] start backend-only instance stack (frontend via host nginx)"
  make up-instance-backend
else
  echo "[deploy] start full instance stack"
  make up-instance
fi

echo "[deploy] run migrations"
make db-migrate

echo "[deploy] health checks"
if [ "$FRONTEND_DEPLOY_MODE" = "standalone" ]; then
  CHECK_WEB=false make health
else
  make health
fi

if [ "$SKIP_API_SMOKE" = "true" ]; then
  echo "[deploy] skip api smoke (SKIP_API_SMOKE=true)"
else
  echo "[deploy] api smoke"
  make api-smoke
fi

echo "[deploy] completed"
