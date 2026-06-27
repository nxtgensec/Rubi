from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class SearchResult:
    document_id: str
    text: str
    score: float
    metadata: dict[str, str]


class KnowledgeSearch(ABC):
    @abstractmethod
    async def index_document(self, document_id: str, text: str, metadata: dict[str, str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        raise NotImplementedError
