#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST_PATH="$ROOT_DIR/pack-registry/manifests/base-profiles.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "[pack-registry-check] jq is required" >&2
  exit 1
fi

echo "[1/4] validate json syntax"
jq . "$MANIFEST_PATH" >/dev/null
jq . "$ROOT_DIR/docs/contracts/base-profile.manifest.schema.json" >/dev/null
jq . "$ROOT_DIR/docs/contracts/tenant-profile.schema.json" >/dev/null

echo "[2/4] validate base profile entrypoint paths"
PROFILE_COUNT=$(jq '.profiles | length' "$MANIFEST_PATH")
if [ "$PROFILE_COUNT" -le 0 ]; then
  echo "[pack-registry-check] manifest has no profiles" >&2
  exit 1
fi

while IFS= read -r path; do
  if [ -z "$path" ] || [ "$path" = "null" ]; then
    continue
  fi
  if [ ! -e "$ROOT_DIR/$path" ]; then
    echo "[pack-registry-check] missing entrypoint: $path" >&2
    exit 1
  fi
done < <(
  jq -r '
    .profiles[]
    | [
        .entrypoints.schema,
        .entrypoints.field_dictionary,
        .entrypoints.workflow,
        .entrypoints.terminology,
        .entrypoints.category_fields,
        .entrypoints.cards,
        .entrypoints.scenarios
      ]
      + (.entrypoints.contracts // [])
    | .[]
  ' "$MANIFEST_PATH"
)

echo "[3/4] validate tenant profile references"
while IFS= read -r tenant_file; do
  [ -f "$tenant_file" ] || continue

  base_profile_id=$(awk -F': ' '/^base_profile_id:/ {gsub(/"/, "", $2); print $2}' "$tenant_file" | tail -n 1)
  if [ -z "$base_profile_id" ]; then
    echo "[pack-registry-check] missing base_profile_id in $tenant_file" >&2
    exit 1
  fi
  if ! jq -e --arg id "$base_profile_id" '.profiles[] | select(.profile_id == $id)' "$MANIFEST_PATH" >/dev/null; then
    echo "[pack-registry-check] unknown base_profile_id=$base_profile_id in $tenant_file" >&2
    exit 1
  fi

  bindings_ref=$(awk -F': ' '/^bindings_ref:/ {gsub(/"/, "", $2); print $2}' "$tenant_file" | tail -n 1)
  if [ -z "$bindings_ref" ]; then
    echo "[pack-registry-check] missing bindings_ref in $tenant_file" >&2
    exit 1
  fi
  if [ ! -f "$ROOT_DIR/$bindings_ref" ]; then
    echo "[pack-registry-check] missing bindings_ref target: $bindings_ref" >&2
    exit 1
  fi

done < <(find "$ROOT_DIR/tenant-config/tenants" -type f \( -name "*.yml" -o -name "*.yaml" \) | sort)

echo "[4/4] run domain-packs consistency check"
python3 "$ROOT_DIR/scripts/validate_domain_packs.py" --root "$ROOT_DIR/domain-packs"

echo "pack-registry-check passed"
