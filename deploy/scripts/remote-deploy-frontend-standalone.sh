#!/usr/bin/env bash
set -euo pipefail

# 在服务器上构建并安装 standalone 前端，避免本地 dist 直传。
# 用法:
#   REPO_DIR=/root/mnt/xiaocai-instance \
#   FRONTEND_API_BASE_URL=/api \
#   API_UPSTREAM_URL=http://127.0.0.1:28001 \
#   bash /root/mnt/xiaocai-instance/deploy/scripts/remote-deploy-frontend-standalone.sh

REPO_DIR=${REPO_DIR:-$HOME/mnt/xiaocai-instance}
WEB_DIR="$REPO_DIR/frame/web"
DOMAIN_PACKS_DIR="$REPO_DIR/domain-packs"
REMOTE_WEB_ROOT=${REMOTE_WEB_ROOT:-/var/www/xiaocai-web}
FRONTEND_API_BASE_URL=${FRONTEND_API_BASE_URL:-/api}
API_UPSTREAM_URL=${API_UPSTREAM_URL:-http://127.0.0.1:28001}
SERVER_NAME=${SERVER_NAME:-_}
TEMPLATE_FILE="$REPO_DIR/deploy/nginx/frontend-standalone-http.conf.template"
NGINX_CONF=${NGINX_CONF:-/etc/nginx/conf.d/xiaocai-frontend.conf}

if [ ! -d "$WEB_DIR" ]; then
  echo "web dir not found: $WEB_DIR"
  exit 1
fi
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "nginx template not found: $TEMPLATE_FILE"
  exit 1
fi
if [ ! -f "$DOMAIN_PACKS_DIR/xiaocai/app-profile.json" ]; then
  echo "domain pack profile not found: $DOMAIN_PACKS_DIR/xiaocai/app-profile.json"
  exit 1
fi

cd "$WEB_DIR"

echo "[frontend] install exact npm dependencies"
npm ci --no-audit --no-fund

echo "[frontend] build standalone frontend"
LOCAL_FLARE_ROOT=/__no_local_flare__ API_BASE_URL="$FRONTEND_API_BASE_URL" ./scripts/build-standalone.sh

if [ ! -d "$WEB_DIR/dist" ]; then
  echo "dist not found after build: $WEB_DIR/dist"
  exit 1
fi

echo "[frontend] install dist -> $REMOTE_WEB_ROOT"
mkdir -p "$REMOTE_WEB_ROOT"
find "$REMOTE_WEB_ROOT" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -a "$WEB_DIR/dist/." "$REMOTE_WEB_ROOT/"

echo "[frontend] install domain-packs -> $REMOTE_WEB_ROOT/domain-packs"
rm -rf "$REMOTE_WEB_ROOT/domain-packs"
cp -a "$DOMAIN_PACKS_DIR" "$REMOTE_WEB_ROOT/domain-packs"

TMP_CONF=$(mktemp)
trap 'rm -f "$TMP_CONF"' EXIT
sed "s|__SERVER_NAME__|$SERVER_NAME|g; s|__API_UPSTREAM__|$API_UPSTREAM_URL|g" "$TEMPLATE_FILE" > "$TMP_CONF"

cp "$TMP_CONF" "$NGINX_CONF"
nginx -t
if ! nginx -s reload; then
  echo "[frontend] warning: nginx reload failed; static assets were installed, and no new nginx process was started"
fi

echo "[frontend] deployed"
