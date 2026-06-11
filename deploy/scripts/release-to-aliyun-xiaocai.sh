#!/usr/bin/env bash
set -euo pipefail

# 正式发布：确认本地已 push -> 服务器 git pull -> 远端 rebuild/recreate -> 远端构建前端
# 用法:
#   git status --short
#   git push origin main
#   REMOTE_HOST=aliyun-xiaocai REMOTE_DIR=/root/mnt/xiaocai-instance \
#     ./deploy/scripts/release-to-aliyun-xiaocai.sh

ROOT_DIR=${ROOT_DIR:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"}
REMOTE_HOST=${REMOTE_HOST:-aliyun-xiaocai}
REMOTE_DIR=${REMOTE_DIR:-/root/mnt/xiaocai-instance}
REMOTE_NAME=${REMOTE_NAME:-origin}
BRANCH=${BRANCH:-}
REMOTE_FORCE_RESET=${REMOTE_FORCE_RESET:-true}
FRONTEND_API_BASE_URL=${FRONTEND_API_BASE_URL:-/api}
API_UPSTREAM_URL=${API_UPSTREAM_URL:-http://127.0.0.1:28001}
SERVER_NAME=${SERVER_NAME:-_}
REMOTE_WEB_ROOT=${REMOTE_WEB_ROOT:-/opt/1panel/apps/openresty/openresty/root}
FRONTEND_DEPLOY_MODE=${FRONTEND_DEPLOY_MODE:-standalone}
FORCE_REBUILD=${FORCE_REBUILD:-true}
FORCE_RECREATE=${FORCE_RECREATE:-true}
INSTANCE_PROJECT=${INSTANCE_PROJECT:-inst-xiaocai-prod}

cd "$ROOT_DIR"

if [ -z "$BRANCH" ]; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi
if [ "$BRANCH" = "HEAD" ]; then
  echo "detached HEAD is not supported for release"
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "local working tree is not clean; commit and push first"
  git status --short
  exit 1
fi

echo "[release] 1/5 verify local branch is pushed: ${REMOTE_NAME}/${BRANCH}"
git fetch "$REMOTE_NAME" "$BRANCH"
LOCAL_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git rev-parse FETCH_HEAD)
if [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
  echo "local HEAD is not pushed to ${REMOTE_NAME}/${BRANCH}"
  echo "local : $LOCAL_HEAD"
  echo "remote: $REMOTE_HEAD"
  exit 1
fi

echo "[release] 2/5 server git pull"
ssh "$REMOTE_HOST" "cd '$REMOTE_DIR' && if [ '$REMOTE_FORCE_RESET' = 'true' ]; then git reset --hard HEAD; fi && git pull --ff-only '$REMOTE_NAME' '$BRANCH'"

echo "[release] 3/5 remote backend deploy"
ssh "$REMOTE_HOST" "INSTANCE_PROJECT='$INSTANCE_PROJECT' REPO_DIR='$REMOTE_DIR' FRONTEND_DEPLOY_MODE='$FRONTEND_DEPLOY_MODE' FORCE_REBUILD='$FORCE_REBUILD' FORCE_RECREATE='$FORCE_RECREATE' bash '$REMOTE_DIR/deploy/scripts/remote-deploy-instance.sh'"

echo "[release] 4/5 remote standalone frontend deploy"
ssh "$REMOTE_HOST" "REPO_DIR='$REMOTE_DIR' REMOTE_WEB_ROOT='$REMOTE_WEB_ROOT' FRONTEND_API_BASE_URL='$FRONTEND_API_BASE_URL' API_UPSTREAM_URL='$API_UPSTREAM_URL' SERVER_NAME='$SERVER_NAME' bash '$REMOTE_DIR/deploy/scripts/remote-deploy-frontend-standalone.sh'"

echo "[release] 5/5 done"
