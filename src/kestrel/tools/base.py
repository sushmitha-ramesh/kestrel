from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    read_only: bool = True
    input_schema: type[BaseModel] | None = None
    output_schema: type[BaseModel] | None = None

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.input_schema is None or self.output_schema is None:
            return self.handler(arguments)
        validated = self.input_schema.model_validate(arguments)
        output = self.handler(validated.model_dump())
        return self.output_schema.model_validate(output).model_dump()