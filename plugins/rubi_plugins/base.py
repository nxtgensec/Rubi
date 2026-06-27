from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    name: str
    description: str

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
