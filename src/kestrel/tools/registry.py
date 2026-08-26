from typing import Any

from .base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.read_only:
            raise ValueError("Kestrel tools must be read-only")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def invoke(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return self.get(name).run(arguments)

    def definitions(self) -> list[dict[str, str]]:
        return [{"name": tool.name, "description": tool.description}
                for tool in self._tools.values()]