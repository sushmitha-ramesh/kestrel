import json
from pathlib import Path
from typing import Any

from .models import ResourceChange, TerraformPlan, redact


def parse_plan(data: dict[str, Any]) -> TerraformPlan:
    changes = []
    for item in data.get("resource_changes", []):
        change = item.get("change", {})
        changes.append(ResourceChange(
            address=item.get("address", "<unknown>"),
            resource_type=item.get("type", "<unknown>"),
            actions=tuple(change.get("actions", [])),
            before=redact(change.get("before")),
            after=redact(change.get("after")),
            after_unknown=redact(change.get("after_unknown")),
            provider=item.get("provider_name") or item.get("provider"),
            sensitive=tuple(change.get("sensitive_attributes", ())),
        ))
    return TerraformPlan(data.get("format_version"), tuple(changes), redact(data.get("variables", {})))


def load_plan(path: str | Path) -> TerraformPlan:
    with Path(path).open(encoding="utf-8") as handle:
        return parse_plan(json.load(handle))