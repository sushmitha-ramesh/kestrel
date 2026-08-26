from .base import AgentContext, Decision


class MockProvider:
    """Scripted provider: request one summary, then stop."""

    def decide(self, context: AgentContext) -> Decision:
        if not context.observations:
            return Decision("tool", "terraform.summary", {}, "Gather plan scope")
        return Decision("final", rationale="Evidence gathered")