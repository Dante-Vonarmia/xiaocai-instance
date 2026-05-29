#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
else
  PYTHON="python3"
fi

echo "[1/8] backend domain and legacy-mainline guards"
(cd "$ROOT_DIR" && "$PYTHON" -m pytest -q \
  adapters/http_api/tests/test_xiaocai_domain_config.py \
  adapters/http_api/tests/test_no_legacy_mainline.py)

echo "[2/8] xiaocai domain-pack sync guard"
FLARE_REPO_PATH="${FLARE_REPO_PATH:-$ROOT_DIR/../F.L.A.R.E}"
FLARE_XIAOCAI_PACK_ROOT="${FLARE_XIAOCAI_PACK_ROOT:-$FLARE_REPO_PATH/domain-packs/xiaocai}"
if [ -d "$FLARE_XIAOCAI_PACK_ROOT" ]; then
  FLARE_XIAOCAI_PACK_ROOT="$FLARE_XIAOCAI_PACK_ROOT" "$ROOT_DIR/scripts/check-xiaocai-pack-sync.sh"
else
  echo "[warn] FLARE xiaocai pack not found, skip sync guard: $FLARE_XIAOCAI_PACK_ROOT"
fi

echo "[3/8] backend patch/action/writeback/e2e parity guards"
(cd "$ROOT_DIR" && "$PYTHON" -m pytest -q \
  adapters/http_api/tests/test_chat_field_candidates.py \
  adapters/http_api/tests/test_chat_core_compat.py \
  adapters/http_api/tests/test_analysis_mode_parity.py \
  adapters/http_api/tests/test_local_e2e_parity.py \
  adapters/http_api/tests/test_chat_stream_projection.py)

echo "[4/8] backend full test suite"
(cd "$ROOT_DIR" && "$PYTHON" -m pytest -q adapters/http_api/tests)

echo "[5/8] frontend unit tests"
(cd "$ROOT_DIR/frame/web" && npm test -- --run)

echo "[6/8] frontend type check"
(cd "$ROOT_DIR/frame/web" && npm run type-check)

echo "[7/8] frontend build"
(cd "$ROOT_DIR/frame/web" && npm run build)

echo "[8/8] FLARE package version parity"
ROOT_DIR="$ROOT_DIR" FLARE_REPO_PATH="${FLARE_REPO_PATH:-$ROOT_DIR/../F.L.A.R.E}" "$PYTHON" - <<'PY'
import json
import os
import sys
from pathlib import Path

root = Path(os.environ["ROOT_DIR"])
web = root / "frame" / "web"
flare_repo = Path(os.environ["FLARE_REPO_PATH"])
packages = ("flare-chat-core", "flare-chat-ui")
package_json = json.loads((web / "package.json").read_text(encoding="utf-8"))
deps = package_json.get("dependencies", {})
problems: list[str] = []

for name in packages:
    expected = str(deps.get(name, "")).strip()
    if not expected:
        problems.append(f"{name}: missing dependency in frame/web/package.json")
        continue

    installed_path = web / "node_modules" / name / "package.json"
    if not installed_path.exists():
        problems.append(f"{name}: node_modules package is not installed")
        continue
    installed = json.loads(installed_path.read_text(encoding="utf-8")).get("version")
    if installed != expected:
        problems.append(f"{name}: package.json expects {expected}, node_modules has {installed}")

    local_path = flare_repo / "packages" / name / "package.json"
    if local_path.exists():
        local = json.loads(local_path.read_text(encoding="utf-8")).get("version")
        if local != expected:
            problems.append(f"{name}: local FLARE source has {local}, frame/web expects {expected}")
    else:
        print(f"[warn] {name}: local FLARE source not found at {local_path}")

if problems:
    print("\n".join(problems), file=sys.stderr)
    sys.exit(1)

print("FLARE package versions are aligned for frame/web, node_modules, and local FLARE source when present.")
PY

echo "xiaocai launch verification passed"
