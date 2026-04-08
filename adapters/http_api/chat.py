"""Compatibility wrapper for gate checks.

Exports the `/chat/run` and `/chat/stream` router without duplicating business logic.
"""

from xiaocai_instance_api.chat.router import router

__all__ = ["router"]
