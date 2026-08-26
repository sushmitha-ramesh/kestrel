from kestrel.llm.base import AgentContext, Provider
from kestrel.tools.registry import ToolRegistry

from .planner import run_loop
from .state import AgentState


def analyze_with_agent(provider: Provider, registry: ToolRegistry, max_rounds: int = 3,
                       context: AgentContext | None = None) -> AgentState:
    """Run bounded evidence gathering; deterministic findings remain authoritative."""
    return run_loop(provider, registry, max_rounds, context)