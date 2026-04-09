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
    )
