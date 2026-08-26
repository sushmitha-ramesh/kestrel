from typing import Any

from kestrel.terraform.models import TerraformPlan

from .base import Tool
from .registry import ToolRegistry


def register_terraform_tools(registry: ToolRegistry, plan: TerraformPlan) -> None:
    def summarize(_: dict[str, Any]) -> dict[str, Any]:
        return {"resources": len(plan.resource_changes), "addresses": [c.address for c in plan.resource_changes]}

    registry.register(Tool("terraform.summary", "Summarize changed Terraform resources", summarize))