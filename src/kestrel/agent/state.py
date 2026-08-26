from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    observations: list[dict[str, Any]] = field(default_factory=list)
    rounds: int = 0
    final: bool = False