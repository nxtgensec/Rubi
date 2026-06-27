from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class PhoneProvider(ABC):
    name: str

    @abstractmethod
    async def make_call(self, to_number: str, agent_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def answer_call(self, call_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def hangup(self, call_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def transfer(self, call_id: str, to_number: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stream_audio(self, call_id: str) -> AsyncIterator[bytes]:
        raise NotImplementedError

    @abstractmethod
    async def start_recording(self, call_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def stop_recording(self, call_id: str) -> str:
        raise NotImplementedError
