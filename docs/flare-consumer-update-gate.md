# FLARE Consumer Update Gate

Status: active

This gate keeps xiaocai aligned with FLARE without patching FLARE-owned UI or
kernel behavior inside xiaocai.

## Principle

- xiaocai consumes released FLARE packages and the FLARE `domain-packs/xiaocai`.
- xiaocai must not hide FLARE chooser/canvas behavior in the frontend as a
  workaround.
- Runtime behavior is verified by probes, not by version strings alone.
- Historical stored payloads are handled by migration/cleanup, not by frontend
  guessing.

## Required checks after each FLARE update

Run these from the xiaocai repo root:

```bash
.venv/bin/python scripts/check_flare_dependency_versions.py
bash scripts/check-xiaocai-pack-sync.sh
.venv/bin/python scripts/verify_flare_consumer_runtime.py --require-flare-root
```

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

Rollback is dependency-pin rollback plus container rebuild; do not patch xiaocai
frontend to compensate for FLARE runtime behavior.
