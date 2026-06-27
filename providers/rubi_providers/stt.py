from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class STTProvider(ABC):
    name: str

    @abstractmethod
    async def transcribe(self, audio: bytes, language: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, audio_chunks: AsyncIterator[bytes]) -> AsyncIterator[str]:
        raise NotImplementedError
