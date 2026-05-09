#!/usr/bin/env bash
set -euo pipefail

# 部署后数据可见性检查。
# 目标：避免上线后因过滤字段/默认模式变化，导致历史项目或会话“数据未丢但不可见”。

python3 - <<'PY'
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def int_env(name, default):
    value = os.getenv(name, "").strip()
    return int(value) if value else default


def request_json(url, token=None, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    method = "POST" if payload is not None else "GET"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code} {body}") from exc


def parse_project_specs(raw_value):
    specs = []
    for raw_item in raw_value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if ":" in item:
            project_id, min_sessions = item.rsplit(":", 1)
            specs.append((project_id.strip(), int(min_sessions.strip())))
        else:
            specs.append((item, 1))
    return specs


def fail(message, summary):
    summary["ok"] = False
    summary["error"] = message
    with open("data-visibility-smoke.log", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(f"[data-visibility] failed: {message}", file=sys.stderr)
    sys.exit(1)


load_dotenv()

summary = {
    "ok": True,
    "enabled": bool_env("DATA_VISIBILITY_SMOKE_ENABLED"),
    "projects": [],
    "checks": [],
}

if not summary["enabled"]:
    print("[data-visibility] skipped (DATA_VISIBILITY_SMOKE_ENABLED is not true)")
    with open("data-visibility-smoke.log", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    sys.exit(0)

api_base_url = os.getenv("DATA_VISIBILITY_SMOKE_API_BASE_URL", "http://localhost:28001").rstrip("/")
auth_mode = os.getenv("DATA_VISIBILITY_SMOKE_AUTH_MODE", "mock").strip()
user_id = os.getenv("DATA_VISIBILITY_SMOKE_USER_ID", "").strip()
function_type = os.getenv("DATA_VISIBILITY_SMOKE_FUNCTION_TYPE", "auto").strip()
project_specs = parse_project_specs(os.getenv("DATA_VISIBILITY_SMOKE_PROJECT_SPECS", ""))
min_projects = int_env("DATA_VISIBILITY_SMOKE_MIN_PROJECTS", 1)
min_total_sessions = int_env("DATA_VISIBILITY_SMOKE_MIN_TOTAL_SESSIONS", 1)

summary.update(
    {
        "api_base_url": api_base_url,
        "auth_mode": auth_mode,
        "user_id": user_id,
        "function_type": function_type,
        "min_projects": min_projects,
        "min_total_sessions": min_total_sessions,
        "project_specs": project_specs,
    }
)

if auth_mode == "mock":
    if not user_id:
        fail("DATA_VISIBILITY_SMOKE_USER_ID is required when auth mode is mock", summary)
    auth_payload = {"mock": True, "mock_user_id": user_id}
elif auth_mode == "root":
    root_token = os.getenv("ROOT_AUTH_TOKEN", "").strip()
    if not root_token:
        fail("ROOT_AUTH_TOKEN is required when auth mode is root", summary)
    auth_payload = {"root_token": root_token}
else:
    fail(f"unsupported DATA_VISIBILITY_SMOKE_AUTH_MODE: {auth_mode}", summary)

auth_json = request_json(f"{api_base_url}/auth/exchange", payload=auth_payload)
token = str(auth_json.get("access_token") or "")
if not token:
    fail("/auth/exchange did not return access_token", summary)

projects_json = request_json(f"{api_base_url}/projects", token=token)
projects = projects_json.get("projects") or []
project_ids = [str(project.get("project_id")) for project in projects if project.get("project_id")]
summary["projects"] = projects

if len(project_ids) < min_projects:
    fail(f"visible project count {len(project_ids)} < expected {min_projects}", summary)

checks = project_specs or [(project_id, 0) for project_id in project_ids]
total_sessions = 0
for project_id, min_sessions in checks:
    query = urllib.parse.urlencode(
        {
            "project_id": project_id,
            "function_type": function_type,
            "page_size": 100,
        }
    )
    sessions_json = request_json(f"{api_base_url}/sessions?{query}", token=token)
    total = int((sessions_json.get("pagination") or {}).get("total") or 0)
    total_sessions += total
    check = {"project_id": project_id, "min_sessions": min_sessions, "actual_sessions": total}
    summary["checks"].append(check)
    if total < min_sessions:
        fail(f"project {project_id} visible sessions {total} < expected {min_sessions}", summary)

summary["total_sessions"] = total_sessions
if total_sessions < min_total_sessions:
    fail(f"visible session count {total_sessions} < expected {min_total_sessions}", summary)

with open("data-visibility-smoke.log", "w", encoding="utf-8") as handle:
    json.dump(summary, handle, ensure_ascii=False, indent=2)

print(
    "[data-visibility] passed: "
    f"projects={len(project_ids)} checked={len(checks)} sessions={total_sessions}"
)
PY
