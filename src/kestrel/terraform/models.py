from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResourceChange:
    address: str
    resource_type: str
    actions: tuple[str, ...]
    before: Any
    after: Any
    after_unknown: Any = None
    provider: str | None = None
    sensitive: tuple[str, ...] = ()

    @property
    def destructive(self) -> bool:
        return "delete" in self.actions or self.actions == ("delete", "create")

    @property
    def replacement(self) -> bool:
        return self.actions in (("delete", "create"), ("create", "delete"))

    @property
    def changed_attributes(self) -> tuple[str, ...]:
        before = self.before if isinstance(self.before, dict) else {}
        after = self.after if isinstance(self.after, dict) else {}
        return tuple(sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key)))


@dataclass(frozen=True)
class TerraformPlan:
    format_version: str | None
    resource_changes: tuple[ResourceChange, ...]
    variables: dict[str, Any] = field(default_factory=dict)


def _redact(value: Any, key: str = "") -> Any:
    sensitive = ("secret", "password", "token", "api_key", "private_key", "access_key", "credential")
    if any(word in key.lower() for word in sensitive):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: _redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v, key) for v in value]
    return value


def redact(value: Any) -> Any:
    """Return a recursively redacted copy suitable for evidence or output."""
    return _redact(value)