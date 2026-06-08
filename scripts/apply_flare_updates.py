#!/usr/bin/env python3
"""Apply resolved FLARE package updates to xiaocai dependency pins."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_PACKAGE_JSON = PROJECT_ROOT / "frame/web/package.json"
HTTP_API_PYPROJECT = PROJECT_ROOT / "adapters/http_api/pyproject.toml"
HTTP_API_REQUIREMENTS = PROJECT_ROOT / "adapters/http_api/requirements.txt"
KERNEL_DOCKERFILE = PROJECT_ROOT / "adapters/kernel/Dockerfile"

TRANSITIVE_NPM_PACKAGES = {"flare-canvas-ui", "flare-generative-ui"}


def load_updates(path: Path | None) -> list[dict[str, Any]]:
    if path:
        return json.loads(path.read_text(encoding="utf-8"))
    completed = subprocess.run(
        ["python", str(PROJECT_ROOT / "scripts/resolve_flare_updates.py"), "--json"],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def update_package_json(updates: list[dict[str, Any]]) -> bool:
    data = json.loads(WEB_PACKAGE_JSON.read_text(encoding="utf-8"))
    changed = False
    for update in updates:
        if update.get("registry") != "npm" or not update.get("update_available"):
            continue
        package = str(update["package"])
        latest = str(update["latest"])
        found = False
        for section in ("dependencies", "devDependencies", "overrides"):
            deps = data.get(section)
            if isinstance(deps, dict) and package in deps:
                found = True
                if deps[package] != latest:
                    deps[package] = latest
                    changed = True
        if not found and package in TRANSITIVE_NPM_PACKAGES:
            data.setdefault("overrides", {})[package] = latest
            data.setdefault("pnpm", {}).setdefault("overrides", {})[package] = latest
            changed = True
    if changed:
        WEB_PACKAGE_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def update_exact_pin(path: Path, package: str, version: str) -> bool:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"(?P<prefix>{re.escape(package)}==)(?P<version>[A-Za-z0-9_.!+-]+)")
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        if match.group("version") == version:
            return match.group(0)
        changed = True
        return f"{match.group('prefix')}{version}"

    new_text = pattern.sub(replace, text)
    if changed:
        path.write_text(new_text, encoding="utf-8")
    return changed


def update_python_pins(updates: list[dict[str, Any]]) -> bool:
    changed = False
    for update in updates:
        if update.get("registry") != "pypi" or not update.get("update_available"):
            continue
        package = str(update["package"])
        latest = str(update["latest"])
        changed = update_exact_pin(HTTP_API_PYPROJECT, package, latest) or changed
        changed = update_exact_pin(HTTP_API_REQUIREMENTS, package, latest) or changed
        changed = update_exact_pin(KERNEL_DOCKERFILE, package, latest) or changed
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-json", type=Path, help="JSON output produced by resolve_flare_updates.py")
    args = parser.parse_args()

    updates = load_updates(args.from_json)
    changed = update_package_json(updates)
    changed = update_python_pins(updates) or changed
    print(json.dumps({"changed": changed}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
