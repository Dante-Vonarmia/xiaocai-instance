from __future__ import annotations


def _as_dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def apply_confidence_policy_to_pending_contract(
    *,
    pending_contract: dict | None,
    confidence_policy: dict | None,
    clarification_policy: dict | None,
    category_prior: dict | None,
    session_id: str,
    mode: str | None,
) -> dict | None:
    policy = _as_dict(confidence_policy)
    if not policy:
        return pending_contract
    if pending_contract:
        merged = dict(pending_contract)
        merged["confidence_policy"] = policy
        return merged

    # Domain score thresholds are advisory until the product evaluation rule is settled.
    # Do not synthesize user-visible pending questions without a FLARE/native pending contract.
    return pending_contract
