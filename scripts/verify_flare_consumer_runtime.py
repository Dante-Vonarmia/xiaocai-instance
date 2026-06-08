#!/usr/bin/env python3
"""Verify xiaocai consumes FLARE runtime behavior expected by release gates."""

from __future__ import annotations

import argparse
import filecmp
import json
import logging
import os
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FLARE_ROOT = PROJECT_ROOT.parent / "F.L.A.R.E"
DEFAULT_MESSAGE = (
    "我需要在上海开展一个端午招商活动，用于和我负责的园区的客户进行客户维系，"
    "预计50人左右，帮我分别做室内室外的方案需求"
)
INLINE_REASON = "candidate_options_inlined_to_main_chain"


@dataclass(frozen=True)
class GateCheck:
    name: str
    passed: bool
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "details": self.details}


def reexec_project_python_when_available() -> None:
    project_python = PROJECT_ROOT / ".venv/bin/python"
    if not project_python.exists():
        return
    if Path(sys.executable).resolve() == project_python.resolve():
        return
    os.execv(str(project_python), [str(project_python), str(Path(__file__).resolve()), *sys.argv[1:]])


def runtime_versions() -> dict[str, str | None]:
    packages = [
        "flare-kernel",
        "flare-kernel-client-py",
        "flare-storage-adapters",
        "flare-engines",
    ]
    result: dict[str, str | None] = {}
    for package in packages:
        try:
            result[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            result[package] = None
    return result


def compare_directories(source: Path, target: Path) -> list[str]:
    differences: list[str] = []
    comparison = filecmp.dircmp(source, target)
    for name in comparison.left_only:
        differences.append(f"source_only:{source / name}")
    for name in comparison.right_only:
        differences.append(f"target_only:{target / name}")
    for name in comparison.diff_files:
        differences.append(f"diff:{target / name}")
    for subdir in comparison.common_dirs:
        differences.extend(compare_directories(source / subdir, target / subdir))
    return differences


def check_domain_pack(flare_root: Path, require_flare_root: bool) -> GateCheck:
    source_pack = flare_root / "domain-packs/xiaocai"
    target_pack = PROJECT_ROOT / "domain-packs/xiaocai"
    if not source_pack.exists():
        return GateCheck(
            name="domain_pack_sync",
            passed=not require_flare_root,
            details={"status": "skipped", "missing_source": str(source_pack)},
        )
    differences = compare_directories(source_pack, target_pack)
    return GateCheck(
        name="domain_pack_sync",
        passed=not differences,
        details={
            "source": str(source_pack),
            "target": str(target_pack),
            "differences": differences[:20],
            "difference_count": len(differences),
        },
    )


def build_probe_runtime(message: str) -> dict[str, Any]:
    logging.getLogger("flare_kernel").setLevel(logging.WARNING)
    from flare_kernel.runtime.orchestration.mode.runtime import build_kernel_runtime

    return build_kernel_runtime(
        trace_id="verify-flare-consumer-runtime",
        tenant_id="tenant-verify-flare-consumer",
        instance_id="xiaocai",
        domain_pack_version="default",
        session_id="session-verify-flare-consumer-runtime",
        intent="auto",
        payload={"domain": "xiaocai", "message": message},
        instance_profile=None,
    )


def check_sidecar_inline_probe(message: str) -> GateCheck:
    runtime = build_probe_runtime(message)
    payload = runtime.get("payload") or {}
    gate = runtime.get("boundary_intent_gate") or {}
    next_action = gate.get("next_action") or {}
    pre_workspace_gate = gate.get("pre_workspace_gate") or {}
    disallowed_projection = {
        "current_question": payload.get("current_question"),
        "question_decision": payload.get("question_decision"),
        "composer_chooser_policy": payload.get("composer_chooser_policy"),
    }
    passed = (
        all(value in (None, {}) for value in disallowed_projection.values())
        and next_action.get("reason") == INLINE_REASON
        and pre_workspace_gate.get("open_canvas_panel") is False
    )
    return GateCheck(
        name="sidecar_options_inline_probe",
        passed=passed,
        details={
            "message": message,
            "disallowed_projection": disallowed_projection,
            "next_action": next_action,
            "pre_workspace_gate": pre_workspace_gate,
            "next_actions": runtime.get("next_actions"),
        },
    )


def run_checks(args: argparse.Namespace) -> list[GateCheck]:
    checks = [
        GateCheck(name="runtime_versions", passed=True, details=runtime_versions()),
        check_domain_pack(Path(args.flare_root).resolve(), args.require_flare_root),
        check_sidecar_inline_probe(args.message),
    ]
    return checks


def print_human(checks: list[GateCheck]) -> None:
    for check in checks:
        status = "OK" if check.passed else "FAIL"
        print(f"[{status}] {check.name}")
        print(json.dumps(check.details, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    reexec_project_python_when_available()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--message", default=DEFAULT_MESSAGE, help="probe message for sidecar inline behavior")
    parser.add_argument("--flare-root", default=str(DEFAULT_FLARE_ROOT), help="local FLARE repo root")
    parser.add_argument(
        "--require-flare-root",
        action="store_true",
        help="fail when the FLARE repo/domain pack source is unavailable",
    )
    args = parser.parse_args(argv)

    checks = run_checks(args)
    if args.json:
        print(json.dumps([check.to_dict() for check in checks], ensure_ascii=False, indent=2))
    else:
        print_human(checks)
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
