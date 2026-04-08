#!/usr/bin/env bash
set -euo pipefail

# 用法:
#   TAG=v1.0.0 REMOTE_HOST=aliyun-xiaocai REMOTE_DIR=/opt/xiaocai-instance \
#   ./deploy/scripts/deploy-from-ghcr.sh

TAG=${TAG:-latest}
REMOTE_HOST=${REMOTE_HOST:-aliyun-xiaocai}
REMOTE_DIR=${REMOTE_DIR:-/opt/xiaocai-instance}
PROJECT=${PROJECT:-inst-xiaocai-test}
IMAGE=${IMAGE:-ghcr.io/dante-vonarmia/xiaocai-instance-api:${TAG}}

echo "[ghcr-deploy] host=${REMOTE_HOST} project=${PROJECT} image=${IMAGE}"

ssh "${REMOTE_HOST}" "
  set -euo pipefail
  cd '${REMOTE_DIR}/deploy'

  if [ ! -f .env ]; then
    echo '.env not found on remote deploy dir'
    exit 1
  fi

  if grep -q '^INST_XIAOCAI_API_IMAGE=' .env; then
    sed -i 's|^INST_XIAOCAI_API_IMAGE=.*|INST_XIAOCAI_API_IMAGE=${IMAGE}|' .env
  else
    echo 'INST_XIAOCAI_API_IMAGE=${IMAGE}' >> .env
  fi

  docker compose -p '${PROJECT}' -f compose.instance.yml pull inst-xiaocai-api
  docker compose -p '${PROJECT}' -f compose.instance.yml up -d --no-build inst-xiaocai-api
  docker compose -p '${PROJECT}' -f compose.instance.yml run --rm --no-deps inst-xiaocai-api python -m xiaocai_instance_api.storage.migrate
  curl -sS http://127.0.0.1:\${API_PORT:-8001}/health
  echo
"

echo "[ghcr-deploy] completed"
