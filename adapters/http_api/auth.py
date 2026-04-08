"""Compatibility wrapper for gate checks.

Exports the `/auth/exchange` router without duplicating business logic.
"""

from xiaocai_instance_api.auth.router import router

__all__ = ["router"]
