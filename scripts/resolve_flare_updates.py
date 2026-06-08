#!/usr/bin/env python3
"""Resolve FLARE package updates available to the xiaocai consumer."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_PACKAGE_JSON = PROJECT_ROOT / "frame/web/package.json"
WEB_PACKAGE_LOCK = PROJECT_ROOT / "frame/web/package-lock.json"
HTTP_API_PYPROJECT = PROJECT_ROOT / "adapters/http_api/pyproject.toml"

NPM_PACKAGES = ["flare-chat-core", "flare-chat-ui", "flare-canvas-ui", "flare-generative-ui"]
PYPI_PACKAGES = ["flare-engines", "flare-kernel", "flare-kernel-client-py", "flare-storage-adapters"]


@dataclass(frozen=True)
class FlareUpdate:
    registry: str
    package: str
    current: str | None
    latest: str | None
    source: str

    @property
    def update_available(self) -> bool:
        return bool(self.current and self.latest and self.current != self.latest)

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "update_available": self.update_available}


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _strip_npm_version(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if text.startswith("npm:") and "@" in text[4:]:
        text = text.rsplit("@", 1)[-1]
    return text.lstrip("^~=")


def current_npm_versions() -> dict[str, tuple[str | None, str]]:
    package_data = _json(WEB_PACKAGE_JSON)
    lock_data = _json(WEB_PACKAGE_LOCK)
    result: dict[str, tuple[str | None, str]] = {}
    for package in NPM_PACKAGES:
        for section in ("dependencies", "devDependencies", "overrides"):
            version = package_data.get(section, {}).get(package)
            if isinstance(version, str):
                result[package] = (_strip_npm_version(version), f"package.json:{section}")
                break
        else:
            locked = lock_data.get("packages", {}).get(f"node_modules/{package}", {}).get("version")
            result[package] = (str(locked) if locked else None, "package-lock")
    return result


def current_pypi_versions() -> dict[str, tuple[str | None, str]]:
    data = tomllib.loads(HTTP_API_PYPROJECT.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    result = {package: (None, "pyproject.toml") for package in PYPI_PACKAGES}
    for dependency in dependencies:
        text = str(dependency).strip()
        if "==" not in text:
            continue
        package, version = text.split("==", 1)
        package = package.strip()
        if package in result:
            result[package] = (version.split(";", 1)[0].strip(), "pyproject.toml")
    return result


def latest_npm_version(package: str) -> str | None:
    completed = subprocess.run(
        ["npm", "view", package, "version", "--silent"],
        cwd=PROJECT_ROOT / "frame/web",
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip() or None


def latest_pypi_version(package: str) -> str | None:
    url = f"https://pypi.org/pypi/{package}/json"
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return str(payload.get("info", {}).get("version") or "").strip() or None


def resolve_updates() -> list[FlareUpdate]:
    npm_current = current_npm_versions()
    pypi_current = current_pypi_versions()
    updates: list[FlareUpdate] = []
    for package in NPM_PACKAGES:
        current, source = npm_current[package]
        updates.append(FlareUpdate("npm", package, current, latest_npm_version(package), source))
    for package in PYPI_PACKAGES:
        current, source = pypi_current[package]
        updates.append(FlareUpdate("pypi", package, current, latest_pypi_version(package), source))
    return updates


def print_human(updates: list[FlareUpdate]) -> None:
    for update in updates:
        status = "UPDATE" if update.update_available else "OK"
        print(
            f"[{status}] {update.registry}:{update.package} "
            f"current={update.current or '<missing>'} latest={update.latest or '<unknown>'} "
            f"source={update.source}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    updates = resolve_updates()
    if args.json:
        print(json.dumps([update.to_dict() for update in updates], ensure_ascii=False, indent=2))
    else:
        print_human(updates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
