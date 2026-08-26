from kestrel.risk.models import RiskReport


def render_console(report: RiskReport) -> str:
    lines = ["Kestrel Infrastructure Review", "", f"FINAL VERDICT: {report.verdict}", ""]
    for finding in report.findings:
        lines.append(f"[{finding.severity.name}] {finding.title} ({finding.rule_id}) "
                 f"Confidence: {finding.confidence}%")
        lines.append(f"  Resource: {finding.resource or 'plan-wide'}")
        lines.append(f"  {finding.description}")
        if finding.recommendation:
            lines.append(f"  Recommendation: {finding.recommendation}")
    return "\n".join(lines)