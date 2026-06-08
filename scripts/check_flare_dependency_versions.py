#!/usr/bin/env python3
"""Check that local FLARE runtime packages match xiaocai pinned versions."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HTTP_API_PYPROJECT = PROJECT_ROOT / "adapters/http_api/pyproject.toml"
PINNED_FLARE_DEP_RE = re.compile(r"^(flare-[A-Za-z0-9_.-]+)==([^;\s]+)")


@dataclass(frozen=True)
class FlareDependencyVersion:
    package: str
    expected: str
    installed: str | None

    @property
    def matches(self) -> bool:
        return self.installed == self.expected

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "matches": self.matches}



def reexec_project_python_when_available() -> None:
    project_venv = PROJECT_ROOT / ".venv"
    project_python = project_venv / "bin/python"
    if not project_python.exists():
        return
    if Path(sys.prefix).resolve() == project_venv.resolve():
        return
    os.execv(str(project_python), [str(project_python), str(Path(__file__).resolve()), *sys.argv[1:]])


def pinned_flare_dependencies(pyproject_path: Path = HTTP_API_PYPROJECT) -> dict[str, str]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    pinned: dict[str, str] = {}
    for dependency in dependencies:
        match = PINNED_FLARE_DEP_RE.match(str(dependency).strip())
        if match:
            pinned[match.group(1)] = match.group(2)
    return pinned


def installed_version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def check_flare_dependency_versions() -> list[FlareDependencyVersion]:
    return [
        FlareDependencyVersion(package=package, expected=expected, installed=installed_version(package))
        for package, expected in sorted(pinned_flare_dependencies().items())
    ]


def drifted_dependencies(results: list[FlareDependencyVersion]) -> list[FlareDependencyVersion]:
    return [result for result in results if not result.matches]


def _print_human(results: list[FlareDependencyVersion]) -> None:
    for result in results:
        status = "OK" if result.matches else "DRIFT"
        installed = result.installed or "<missing>"
        print(f"[{status}] {result.package}: installed={installed} expected={result.expected}")


def main(argv: list[str] | None = None) -> int:
    reexec_project_python_when_available()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    results = check_flare_dependency_versions()
    drifted = drifted_dependencies(results)
    if args.json:
        print(json.dumps([result.to_dict() for result in results], ensure_ascii=False, indent=2))
    else:
        _print_human(results)
        if drifted:
            print("\nRun: .venv/bin/pip install -e adapters/http_api", file=sys.stderr)
    return 1 if drifted else 0


if __name__ == "__main__":
    raise SystemExit(main())
