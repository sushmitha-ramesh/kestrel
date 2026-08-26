from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Decision:
    kind: str
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    rationale: str = ""


@dataclass(frozen=True)
class AgentContext:
    observations: list[dict[str, Any]]
    available_tools: list[dict[str, str]]
    deterministic_findings: list[dict[str, Any]]
    plan_summary: dict[str, Any]


class Provider(Protocol):
    def decide(self, context: AgentContext) -> Decision: ...