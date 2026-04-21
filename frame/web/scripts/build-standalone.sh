#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_BASE_URL=${API_BASE_URL:-/api}
CORE_ENTRY_URL=${CORE_ENTRY_URL:-/core/}

if [ ! -f package.json ]; then
  echo "package.json not found in $ROOT_DIR"
  exit 1
fi

if [ ! -d node_modules ]; then
  npm ci --no-audit --no-fund
fi

VITE_API_BASE_URL="$API_BASE_URL" VITE_FLARE_CORE_ENTRY_URL="$CORE_ENTRY_URL" npm run build

echo "build complete: $ROOT_DIR/dist (VITE_API_BASE_URL=$API_BASE_URL, VITE_FLARE_CORE_ENTRY_URL=$CORE_ENTRY_URL)"
