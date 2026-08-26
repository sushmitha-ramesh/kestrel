import json
from dataclasses import asdict

from kestrel.risk.models import RiskReport


def render_json(report: RiskReport) -> str:
    payload = {"verdict": report.verdict, "summary": {"finding_count": len(report.findings)},
               "findings": [asdict(f) | {"severity": f.severity.name} for f in report.findings],
               "agent_steps": list(report.agent_steps), "metadata": {"version": "0.1.0"}}
    return json.dumps(payload, indent=2, sort_keys=True)