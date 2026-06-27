from datetime import datetime

from pydantic import BaseModel


class KnowledgeDocumentRead(BaseModel):
    id: str
    name: str
    source_type: str
    status: str
    chunks: int
    created_at: datetime
