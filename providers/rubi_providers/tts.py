from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class TTSProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, text: str, voice: str, language: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, text: str, voice: str, language: str) -> AsyncIterator[bytes]:
        raise NotImplementedError
