from typing import Any

from .models import ResourceChange


def flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    result: dict[str, Any] = {}
    for key, child in value.items():
        path = f"{prefix}.{key}" if prefix else key
        result.update(flatten(child, path))
    return result


def change_evidence(change: ResourceChange) -> dict[str, Any]:
    return {"address": change.address, "type": change.resource_type,
            "actions": list(change.actions), "before": change.before, "after": change.after}