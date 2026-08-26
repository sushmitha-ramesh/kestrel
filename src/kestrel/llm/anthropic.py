from .providers import UnavailableProvider


class AnthropicProvider(UnavailableProvider):
    """Provider seam for a future structured Anthropic implementation."""

    def __init__(self) -> None:
        super().__init__("Anthropic")