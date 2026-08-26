from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


class Severity(IntEnum):
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Verdict(str, Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    severity: Severity
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""
    positive: bool = False
    confidence: int = 90
    resource: str = ""


@dataclass(frozen=True)
class RiskReport:
    findings: tuple[Finding, ...]
    verdict: Verdict
    agent_steps: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_findings(cls, findings: list[Finding]) -> "RiskReport":
        maximum = max((f.severity for f in findings), default=Severity.INFO)
        verdict = Verdict.BLOCK if maximum == Severity.CRITICAL else Verdict.REVIEW if maximum >= Severity.HIGH else Verdict.APPROVE
        return cls(tuple(findings), verdict)