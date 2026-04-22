#!/usr/bin/env bash
set -euo pipefail

# 一键串联：上传代码 -> 远端 instance 部署 -> 前端独立部署
# 用法:
#   FRONTEND_API_BASE_URL=/api \
#   API_UPSTREAM_URL=http://127.0.0.1:8001 \
#   ROOT_DIR=/Users/xxx/Development/procurement-agents \
#   ./deploy/scripts/release-to-aliyun-xiaocai.sh

ROOT_DIR=${ROOT_DIR:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"}
REMOTE_HOST=${REMOTE_HOST:-aliyun-xiaocai}
REMOTE_DIR=${REMOTE_DIR:-~/mnt/xiaocai-instance}
FRONTEND_API_BASE_URL=${FRONTEND_API_BASE_URL:-/api}
API_UPSTREAM_URL=${API_UPSTREAM_URL:-http://127.0.0.1:8001}
SERVER_NAME=${SERVER_NAME:-_}
COPY_PROD_ENV=${COPY_PROD_ENV:-false}
FRONTEND_DEPLOY_MODE=${FRONTEND_DEPLOY_MODE:-standalone}

cd "$ROOT_DIR"

echo "[release] 1/5 upload repository"
REMOTE_HOST="$REMOTE_HOST" REMOTE_DIR="$REMOTE_DIR" ./deploy/scripts/upload-instance-to-aliyun-xiaocai.sh

if [ "$COPY_PROD_ENV" = "true" ]; then
  if [ ! -f "$ROOT_DIR/deploy/.env.production" ]; then
    echo "COPY_PROD_ENV=true but deploy/.env.production not found"
    exit 1
  fi
  echo "[release] copy deploy/.env.production -> remote deploy/.env"
  scp "$ROOT_DIR/deploy/.env.production" "$REMOTE_HOST:$REMOTE_DIR/deploy/.env"
fi

echo "[release] 2/5 remote backend deploy"
ssh "$REMOTE_HOST" "REPO_DIR='$REMOTE_DIR' FRONTEND_DEPLOY_MODE='$FRONTEND_DEPLOY_MODE' bash '$REMOTE_DIR/deploy/scripts/remote-deploy-instance.sh'"

echo "[release] 3/5 build standalone frontend"
cd "$ROOT_DIR/frame/web"
API_BASE_URL="$FRONTEND_API_BASE_URL" ./scripts/build-standalone.sh

echo "[release] 4/5 deploy standalone frontend"
cd "$ROOT_DIR"
REMOTE_HOST="$REMOTE_HOST" API_UPSTREAM_URL="$API_UPSTREAM_URL" SERVER_NAME="$SERVER_NAME" \
  ./deploy/scripts/deploy-frontend-standalone-to-aliyun-xiaocai.sh

echo "[release] 5/5 done"
