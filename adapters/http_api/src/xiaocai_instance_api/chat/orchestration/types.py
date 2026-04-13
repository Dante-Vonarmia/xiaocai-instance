from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class LocalOrchestrationResult:
    message: str
    cards: List[dict]
    metadata: Dict[str, object]
    pending_contract: Dict[str, object] | None
