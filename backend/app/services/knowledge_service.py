from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.knowledge import KnowledgeDocumentRead


class KnowledgeService:
    def __init__(self) -> None:
        self._documents: list[KnowledgeDocumentRead] = []

    async def list_documents(self) -> list[KnowledgeDocumentRead]:
        return self._documents

    async def register_document(self, name: str, source_type: str) -> KnowledgeDocumentRead:
        document = KnowledgeDocumentRead(
            id=str(uuid4()),
            name=name,
            source_type=source_type,
            status="queued",
            chunks=0,
            created_at=datetime.now(UTC),
        )
        self._documents.append(document)
        return document


knowledge_service = KnowledgeService()
