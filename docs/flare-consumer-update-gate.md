# FLARE Consumer Update Gate

Status: active

This gate keeps xiaocai aligned with FLARE without patching FLARE-owned UI or
kernel behavior inside xiaocai.

## Principle

- xiaocai consumes released FLARE packages and the FLARE `domain-packs/xiaocai`.
- For xiaocai, FLARE is treated as a black box except for published contracts.
- Domain packs are currently developed, tested, and contract-verified on the
  FLARE side before xiaocai syncs or consumes them.
- xiaocai must not hide FLARE chooser/canvas behavior in the frontend as a
  workaround.
- xiaocai must not add local rules, fallbacks, shims, aliases, or heuristics to
  compensate for a FLARE behavior mismatch.
- Runtime behavior is verified by probes, not by version strings alone.
- Historical stored payloads are handled by migration/cleanup, not by frontend
  guessing.

## User-facing update baseline

xiaocai should present FLARE capability changes as an update of the deployed
instance shell:

1. detect available FLARE/package/domain-pack release state;
2. show the user that an update is available;
3. apply dependency/domain-pack sync without changing xiaocai behavior rules;
4. rebuild/redeploy the instance;
5. run runtime probes on the deployed target;
6. mark success only after probes pass, otherwise roll back dependency pins and
   rebuild from the previous known-good state.

The update path may preserve xiaocai-owned auth, persistence, connectors,
tenant/user configuration, and data governance assets. It must not introduce
new local domain/runtime/capability logic.

## Required checks after each FLARE update

Run these from the xiaocai repo root:

```bash
.venv/bin/python scripts/check_flare_dependency_versions.py
bash scripts/check-xiaocai-pack-sync.sh
.venv/bin/python scripts/verify_flare_consumer_runtime.py --require-flare-root
```

## Fixed local refresh flow

After changing FLARE dependency pins, refresh local xiaocai from `deploy/`:

```bash
make flare-refresh-local
```

This target removes frontend install/build artifacts, clears npm cache, runs
`npm ci`, rebuilds kernel/api/web images with Docker `--no-cache`, force
recreates the xiaocai runtime containers, runs health checks, and prints the
container-side `flare-kernel` version.

It intentionally preserves Postgres/Redis/Qdrant volumes. Do not use `down -v`
for normal FLARE package updates unless a separate data reset is explicitly
approved.

## Scheduled update monitor

The GitHub workflow `.github/workflows/flare-update-monitor.yml` runs daily and
can also be run manually.

- `action=check`: detect newer FLARE packages and write the result to the
  workflow summary.
- `action=apply`: align xiaocai pins to the latest published FLARE packages,
  refresh npm lockfile, run gates/build, and open a PR.

Local equivalent:

```bash
.venv/bin/python scripts/resolve_flare_updates.py
.venv/bin/python scripts/resolve_flare_updates.py --json > /tmp/flare-updates.json
.venv/bin/python scripts/apply_flare_updates.py --from-json /tmp/flare-updates.json
```

`apply_flare_updates.py` only changes dependency pins. It does not modify
xiaocai frontend behavior, procurement workflow logic, or FLARE kernel code.

The runtime verifier must pass:

- `domain_pack_sync`
- `sidecar_options_inline_probe`

The sidecar probe confirms that a new xiaocai procurement intake turn:

- does not project `current_question`
- does not project `question_decision`
- does not project `composer_chooser_policy`
- returns `candidate_options_inlined_to_main_chain`
- keeps `open_canvas_panel=false`

## Local/online deployment smoke

After rebuilding local or online containers, run the same runtime probe inside
the API container:

```bash
docker exec inst-xiaocai-api python scripts/verify_flare_consumer_runtime.py
```

If the script is not present in the container image, run the equivalent kernel
probe before marking the deploy verified.

## Historical payload rule

Old sessions may already contain:

- `current_question`
- `composer_chooser_policy`
- `composer_ui.composer_chooser.visible=true`

These are stored payloads. Do not hide them in the frontend. Use one of:

- backend migration/cleanup
- mark the question stale/dismissed/answered
- archive/reset affected sessions during testing

## Release acceptance

A FLARE update is accepted by xiaocai only when:

1. FLARE dependency pins are intentional.
2. `domain-packs/xiaocai` is byte-aligned with FLARE.
3. Runtime probe passes locally.
4. Runtime probe passes on the deployed target.
5. Any historical payload cleanup is explicitly recorded.
6. No xiaocai-side rule, fallback, shim, alias, or heuristic was added to make
   the update pass.

Rollback is dependency-pin rollback plus container rebuild; do not patch xiaocai
frontend to compensate for FLARE runtime behavior.
