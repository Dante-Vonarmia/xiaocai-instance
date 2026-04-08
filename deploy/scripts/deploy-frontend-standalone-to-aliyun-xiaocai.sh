#!/usr/bin/env bash
set -euo pipefail

# 前端独立部署到远端 Nginx（HTTP 首发）
# 本地执行，要求 frame/web/dist 已构建
# 用法:
#   REMOTE_HOST=aliyun-xiaocai API_BASE_URL=http://47.101.138.75:8001 SERVER_NAME=_ ./deploy/scripts/deploy-frontend-standalone-to-aliyun-xiaocai.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_HOST=${REMOTE_HOST:-aliyun-xiaocai}
REMOTE_WEB_ROOT=${REMOTE_WEB_ROOT:-/var/www/xiaocai-web}
SERVER_NAME=${SERVER_NAME:-_}
API_BASE_URL=${API_BASE_URL:-}

DIST_DIR="$ROOT_DIR/frame/web/dist"
TEMPLATE_FILE="$ROOT_DIR/deploy/nginx/frontend-standalone-http.conf.template"

if [ -z "$API_BASE_URL" ]; then
  echo "API_BASE_URL is required, e.g. http://47.101.138.75:8001"
  exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
  echo "dist not found: $DIST_DIR"
  echo "run: cd frame/web && API_BASE_URL=$API_BASE_URL ./scripts/build-standalone.sh"
  exit 1
fi

if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "template not found: $TEMPLATE_FILE"
  exit 1
fi

TMP_CONF=$(mktemp)
trap 'rm -f "$TMP_CONF"' EXIT

sed "s|__SERVER_NAME__|$SERVER_NAME|g; s|__API_BASE_URL__|$API_BASE_URL|g" "$TEMPLATE_FILE" > "$TMP_CONF"

echo "[frontend] upload dist -> ${REMOTE_HOST}:${REMOTE_WEB_ROOT}"
ssh "$REMOTE_HOST" "mkdir -p '$REMOTE_WEB_ROOT'"

LOCAL_RSYNC=false
REMOTE_RSYNC=false
if command -v rsync >/dev/null 2>&1; then
  LOCAL_RSYNC=true
fi
if ssh "$REMOTE_HOST" "command -v rsync >/dev/null 2>&1"; then
  REMOTE_RSYNC=true
fi

if [ "$LOCAL_RSYNC" = true ] && [ "$REMOTE_RSYNC" = true ]; then
  rsync -az --delete "$DIST_DIR/" "$REMOTE_HOST:$REMOTE_WEB_ROOT/"
else
  ssh "$REMOTE_HOST" "find '$REMOTE_WEB_ROOT' -mindepth 1 -maxdepth 1 -exec rm -rf {} +"
  tar -C "$DIST_DIR" -cf - . | ssh "$REMOTE_HOST" "tar -C '$REMOTE_WEB_ROOT' -xf -"
fi

echo "[frontend] install nginx site config"
scp "$TMP_CONF" "$REMOTE_HOST:/etc/nginx/conf.d/xiaocai-frontend.conf"

ssh "$REMOTE_HOST" "nginx -t && nginx -s reload"

echo "[frontend] deployed"
