#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_BASE_URL=${API_BASE_URL:-}
if [ -z "$API_BASE_URL" ]; then
  echo "usage: API_BASE_URL=http://<server-ip>:8001 ./scripts/build-standalone.sh"
  exit 1
fi

if [ ! -f package.json ]; then
  echo "package.json not found in $ROOT_DIR"
  exit 1
fi

if [ ! -d node_modules ]; then
  npm ci --no-audit --no-fund
fi

VITE_API_BASE_URL="$API_BASE_URL" npm run build

echo "build complete: $ROOT_DIR/dist"
