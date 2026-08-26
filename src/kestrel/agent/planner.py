from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from kestrel.llm.base import AgentContext, Decision, Provider
from kestrel.tools.registry import ToolRegistry

from .state import AgentState


class GraphState(TypedDict):
    observations: list[dict[str, Any]]
    rounds: int
    final: bool


def run_loop(provider: Provider, registry: ToolRegistry, max_rounds: int = 3,
             context: AgentContext | None = None) -> AgentState:
    base_context = context or AgentContext([], [], [], {})

    def step(state: GraphState) -> dict[str, Any]:
        if state["rounds"] >= max_rounds:
            return {"final": True}
        used_tools = {item.get("tool") for item in state["observations"] if item.get("tool")}
        available_tools = [tool for tool in base_context.available_tools
                           if tool.get("name") not in used_tools]
        decision: Decision = provider.decide(AgentContext(
            state["observations"],
            available_tools,
            base_context.deterministic_findings,
            base_context.plan_summary,
        ))
        observations = list(state["observations"])
        rounds = state["rounds"] + 1
        if decision.kind != "tool" or not decision.tool_name:
            return {"rounds": rounds, "final": True}
        if decision.tool_name not in registry.names():
            observations.append({"error": f"unregistered tool: {decision.tool_name}",
                                 "reason": decision.rationale})
            return {"observations": observations, "rounds": rounds, "final": True}
        arguments = decision.arguments or {}
        duplicate = any(item.get("tool") == decision.tool_name and
                        item.get("arguments") == arguments for item in observations)
        if duplicate:
            observations.append({"error": "duplicate tool request; no new evidence available",
                                 "tool": decision.tool_name, "reason": decision.rationale})
            return {"observations": observations, "rounds": rounds, "final": True}
        observations.append({"tool": decision.tool_name, "reason": decision.rationale,
                             "arguments": arguments,
                             "observation": registry.invoke(decision.tool_name, arguments)})
        return {"observations": observations, "rounds": rounds}

    def continue_or_end(state: GraphState) -> str:
        return END if state["final"] or state["rounds"] >= max_rounds else "step"

    graph = StateGraph(GraphState)
    graph.add_node("step", step)
    graph.add_edge(START, "step")
    graph.add_conditional_edges("step", continue_or_end, {"step": "step", END: END})
    result = graph.compile().invoke({"observations": [], "rounds": 0, "final": False})
    return AgentState(result["observations"], result["rounds"], result["final"])