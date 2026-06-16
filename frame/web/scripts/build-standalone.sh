#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_BASE_URL=${API_BASE_URL:-/api}
CORE_ENTRY_URL=${CORE_ENTRY_URL:-/core/}
ENABLE_PUBLIC_TEST_AUTH=${ENABLE_PUBLIC_TEST_AUTH:-${VITE_ENABLE_PUBLIC_TEST_AUTH:-false}}
PUBLIC_TEST_USER_ID=${PUBLIC_TEST_USER_ID:-${VITE_PUBLIC_TEST_USER_ID:-public-test-user}}
PUBLIC_TEST_DISPLAY_NAME=${PUBLIC_TEST_DISPLAY_NAME:-${VITE_PUBLIC_TEST_DISPLAY_NAME:-云鹤AI公开测试用户}}

if [ ! -f package.json ]; then
  echo "package.json not found in $ROOT_DIR"
  exit 1
fi

if [ ! -d node_modules ]; then
  npm ci --no-audit --no-fund
fi

resolve_package_version() {
  node - "$1" <<'NODE'
const fs = require('node:fs');

const packageName = process.argv[2];
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const packageLock = JSON.parse(fs.readFileSync('package-lock.json', 'utf8'));
const packages = packageLock.packages || {};
const packageNode = packages[`node_modules/${packageName}`] || {};
const version = (
  packageJson.overrides?.[packageName]
  || packageJson.pnpm?.overrides?.[packageName]
  || packageNode.version
  || packageJson.dependencies?.[packageName]
  || packageJson.devDependencies?.[packageName]
);

if (!version) {
  console.error(`Cannot resolve ${packageName} from package.json/package-lock.json`);
  process.exit(1);
}

console.log(String(version).replace(/^[~^=]/, ''));
NODE
}

LOCAL_FLARE_ROOT="${LOCAL_FLARE_ROOT:-$ROOT_DIR/../../../F.L.A.R.E}"
if [ -f "$LOCAL_FLARE_ROOT/packages/flare-chat-core/package.json" ] && [ -f "$LOCAL_FLARE_ROOT/packages/flare-chat-ui/package.json" ]; then
  FLARE_CANVAS_UI_VERSION="$(resolve_package_version flare-canvas-ui)"
  FLARE_GENERATIVE_UI_VERSION="$(resolve_package_version flare-generative-ui)"
  echo "using local FLARE packages with flare-canvas-ui@$FLARE_CANVAS_UI_VERSION flare-generative-ui@$FLARE_GENERATIVE_UI_VERSION"
  npm install --no-save \
    flare-chat-core@file:"$LOCAL_FLARE_ROOT/packages/flare-chat-core" \
    flare-chat-ui@file:"$LOCAL_FLARE_ROOT/packages/flare-chat-ui" \
    flare-canvas-ui@"$FLARE_CANVAS_UI_VERSION" \
    flare-generative-ui@"$FLARE_GENERATIVE_UI_VERSION"
fi

VITE_API_BASE_URL="$API_BASE_URL" \
  VITE_FLARE_CORE_ENTRY_URL="$CORE_ENTRY_URL" \
  VITE_ENABLE_PUBLIC_TEST_AUTH="$ENABLE_PUBLIC_TEST_AUTH" \
  VITE_PUBLIC_TEST_USER_ID="$PUBLIC_TEST_USER_ID" \
  VITE_PUBLIC_TEST_DISPLAY_NAME="$PUBLIC_TEST_DISPLAY_NAME" \
  npm run build

DIST_BUNDLE=$(find "$ROOT_DIR/dist/assets" -maxdepth 1 -name 'index-*.js' | head -n 1)
if [ -z "${DIST_BUNDLE:-}" ]; then
  echo "built bundle not found under $ROOT_DIR/dist/assets"
  exit 1
fi

node ./scripts/patch-flare-chat-core.cjs "$DIST_BUNDLE"

echo "build complete: $ROOT_DIR/dist (VITE_API_BASE_URL=$API_BASE_URL, VITE_FLARE_CORE_ENTRY_URL=$CORE_ENTRY_URL, VITE_ENABLE_PUBLIC_TEST_AUTH=$ENABLE_PUBLIC_TEST_AUTH)"
