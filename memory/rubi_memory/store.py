from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class CallerMemory:
    caller_id: str
    language: str
    summary: str
    preferences: dict[str, str]
    lead_status: str | None = None


class MemoryStore(ABC):
    @abstractmethod
    async def get_caller_memory(self, caller_id: str) -> CallerMemory | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_caller_memory(self, memory: CallerMemory) -> None:
        raise NotImplementedError
