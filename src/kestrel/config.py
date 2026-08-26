import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    aws_profile: str | None = None
    region: str | None = None
    max_tool_rounds: int = 3
    llm_provider: str = "mock"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(os.getenv("AWS_PROFILE"), os.getenv("AWS_REGION"),
               int(os.getenv("KESTREL_MAX_AGENT_STEPS", "8")),
               os.getenv("KESTREL_LLM_PROVIDER", "mock"))