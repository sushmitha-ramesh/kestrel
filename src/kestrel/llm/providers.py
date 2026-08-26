from .base import AgentContext, Decision, Provider


class UnavailableProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    def decide(self, context: AgentContext) -> Decision:
        return Decision("final", rationale=f"{self.name} adapter unavailable; deterministic analysis retained")


def provider_for(name: str) -> Provider:
    if name == "mock":
        from .mock import MockProvider
        return MockProvider()
    if name == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider()
    if name == "openai":
        from .openai import OpenAIProvider
        return OpenAIProvider()
    return UnavailableProvider(name)