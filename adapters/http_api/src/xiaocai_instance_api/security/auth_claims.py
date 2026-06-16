"""
认证声明模型
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthClaims:
    user_id: str
    tenant_id: str | None = None
    org_id: str | None = None
    roles: tuple[str, ...] = ("user",)
    source: str | None = None
    display_name: str | None = None
    member_status: str | None = None
    external_user_id: str | None = None
    last_login_at: str | None = None

    def has_role(self, role: str) -> bool:
        return role in self.roles


def claims_from_payload(payload: dict[str, Any]) -> AuthClaims:
    user_id = str(payload.get("sub") or "").strip()
    if not user_id:
        raise ValueError("Missing user_id in token payload")

    tenant_id = payload.get("tenant_id")
    if tenant_id is not None:
        tenant_id = str(tenant_id).strip() or None

    org_id = payload.get("org_id")
    if org_id is not None:
        org_id = str(org_id).strip() or None

    raw_roles = payload.get("roles")
    if isinstance(raw_roles, list):
        roles = tuple(str(item).strip() for item in raw_roles if str(item).strip())
    elif isinstance(raw_roles, str) and raw_roles.strip():
        roles = (raw_roles.strip(),)
    else:
        roles = ("user",)

    return AuthClaims(
        user_id=user_id,
        tenant_id=tenant_id,
        org_id=org_id,
        roles=roles,
        source=_optional_text(payload.get("source")),
        display_name=_optional_text(payload.get("display_name")),
        member_status=_optional_text(payload.get("member_status")),
        external_user_id=_optional_text(payload.get("external_user_id")),
        last_login_at=_optional_text(payload.get("last_login_at")),
    )


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None
