from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def embeddings(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
