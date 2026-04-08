"""Compatibility wrapper for gate checks.

Keeps `/auth/exchange`, `/chat/run`, and `/chat/stream` discoverable without copying logic.
"""

from xiaocai_instance_api.app import create_app
from xiaocai_instance_api.main import main

__all__ = ["create_app", "main"]

if __name__ == "__main__":
    main()
