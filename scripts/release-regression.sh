#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON="$ROOT_DIR/.venv/bin/python"
else
  PYTHON="python3"
fi

echo "[1/2] release regression: adapters/http_api/tests/test_release_regression.py"
(cd "$ROOT_DIR/adapters/http_api" && "$PYTHON" -m pytest -q tests/test_release_regression.py)

echo "[2/2] full gate"
(cd "$ROOT_DIR" && bash scripts/req-001-check.sh)

echo "release regression passed"
