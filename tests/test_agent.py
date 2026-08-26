from kestrel.agent.planner import run_loop
from kestrel.llm.mock import MockProvider
from kestrel.terraform.parser import parse_plan
from kestrel.tools.registry import ToolRegistry
from kestrel.tools.terraform_tools import register_terraform_tools


def test_mock_loop_is_bounded_and_uses_registered_tool() -> None:
    registry = ToolRegistry()
    register_terraform_tools(registry, parse_plan({"resource_changes": []}))
    state = run_loop(MockProvider(), registry, max_rounds=2)
    assert state.rounds == 2
    assert state.observations[0]["tool"] == "terraform.summary"