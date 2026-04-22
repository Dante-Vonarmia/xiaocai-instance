#!/usr/bin/env bash
set -euo pipefail

# 从本地上传 xiaocai instance 仓库到远端（默认 aliyun-xiaocai）
# 用法:
#   REMOTE_HOST=aliyun-xiaocai REMOTE_DIR=~/mnt/xiaocai-instance ./scripts/upload-instance-to-aliyun-xiaocai.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REMOTE_HOST=${REMOTE_HOST:-aliyun-xiaocai}
REMOTE_DIR=${REMOTE_DIR:-~/mnt/xiaocai-instance}
export COPYFILE_DISABLE=1

echo "[upload] ensure remote dir: ${REMOTE_HOST}:${REMOTE_DIR}"
ssh "$REMOTE_HOST" "mkdir -p '$REMOTE_DIR'"

LOCAL_RSYNC=false
REMOTE_RSYNC=false
if command -v rsync >/dev/null 2>&1; then
  LOCAL_RSYNC=true
fi
if ssh "$REMOTE_HOST" "command -v rsync >/dev/null 2>&1"; then
  REMOTE_RSYNC=true
fi

if [ "$LOCAL_RSYNC" = true ] && [ "$REMOTE_RSYNC" = true ]; then
  echo "[upload] syncing repository via rsync to ${REMOTE_HOST}:${REMOTE_DIR}"
  rsync -az --delete \
    --exclude '.DS_Store' \
    --exclude '.venv/' \
    --exclude 'frame/web/node_modules/' \
    --exclude 'frame/web/dist/' \
    --exclude 'docs/archive/' \
    --exclude 'deploy/backups/' \
    --exclude 'deploy/*.log' \
    --exclude 'deploy/.env' \
    "$ROOT_DIR/" "$REMOTE_HOST:$REMOTE_DIR/"
else
  echo "[upload] rsync unavailable on local/remote, fallback to tar stream"
  tar \
    --exclude='.DS_Store' \
    --exclude='.venv' \
    --exclude='frame/web/node_modules' \
    --exclude='frame/web/dist' \
    --exclude='docs/archive' \
    --exclude='deploy/backups' \
    --exclude='deploy/*.log' \
    --exclude='deploy/.env' \
    -C "$ROOT_DIR" -cf - . | ssh "$REMOTE_HOST" "tar -C '$REMOTE_DIR' -xf -"
fi

echo "[upload] done"
