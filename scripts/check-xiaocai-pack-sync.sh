#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLARE_REPO_PATH="${FLARE_REPO_PATH:-$ROOT_DIR/../F.L.A.R.E}"
SOURCE_PACK="${FLARE_XIAOCAI_PACK_ROOT:-$FLARE_REPO_PATH/domain-packs/xiaocai}"
TARGET_PACK="${XIAOCAI_PACK_ROOT:-$ROOT_DIR/domain-packs/xiaocai}"

if [ ! -d "$SOURCE_PACK" ]; then
  echo "[xiaocai-pack-sync] FLARE xiaocai pack not found: $SOURCE_PACK" >&2
  echo "[xiaocai-pack-sync] set FLARE_REPO_PATH or FLARE_XIAOCAI_PACK_ROOT" >&2
  exit 1
fi

if [ ! -d "$TARGET_PACK" ]; then
  echo "[xiaocai-pack-sync] local xiaocai pack not found: $TARGET_PACK" >&2
  exit 1
fi

if ! diff -qr "$SOURCE_PACK" "$TARGET_PACK"; then
  echo "[xiaocai-pack-sync] domain-packs/xiaocai is out of sync with FLARE" >&2
  echo "[xiaocai-pack-sync] sync command:" >&2
  echo "  rsync -a --delete '$SOURCE_PACK/' '$TARGET_PACK/'" >&2
  exit 1
fi

echo "[xiaocai-pack-sync] domain-packs/xiaocai is aligned with FLARE: $SOURCE_PACK"
