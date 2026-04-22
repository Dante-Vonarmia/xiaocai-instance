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

LOCAL_FLARE_ROOT="${LOCAL_FLARE_ROOT:-$ROOT_DIR/../../../F.L.A.R.E}"
if [ -f "$LOCAL_FLARE_ROOT/packages/flare-chat-core/package.json" ] && [ -f "$LOCAL_FLARE_ROOT/packages/flare-chat-ui/package.json" ]; then
  npm install --no-save \
    @flare/chat-core@file:"$LOCAL_FLARE_ROOT/packages/flare-chat-core" \
    @flare/chat-ui@file:"$LOCAL_FLARE_ROOT/packages/flare-chat-ui" \
    flare-canvas-ui@0.2.3 \
    flare-generative-ui@0.2.2
fi

VITE_API_BASE_URL="$API_BASE_URL" VITE_FLARE_CORE_ENTRY_URL="$CORE_ENTRY_URL" npm run build

DIST_BUNDLE=$(find "$ROOT_DIR/dist/assets" -maxdepth 1 -name 'index-*.js' | head -n 1)
if [ -z "${DIST_BUNDLE:-}" ]; then
  echo "built bundle not found under $ROOT_DIR/dist/assets"
  exit 1
fi

node ./scripts/patch-flare-chat-core.cjs "$DIST_BUNDLE"

echo "build complete: $ROOT_DIR/dist (VITE_API_BASE_URL=$API_BASE_URL, VITE_FLARE_CORE_ENTRY_URL=$CORE_ENTRY_URL)"
