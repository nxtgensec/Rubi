from app.schemas.knowledge import KnowledgeDocumentRead
from app.services.knowledge_service import knowledge_service
from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.get("", response_model=list[KnowledgeDocumentRead])
async def list_documents() -> list[KnowledgeDocumentRead]:
    return await knowledge_service.list_documents()


@router.post("/upload", response_model=KnowledgeDocumentRead, status_code=202)
async def upload_document(file: UploadFile) -> KnowledgeDocumentRead:
    source_type = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "unknown"
    return await knowledge_service.register_document(
        name=file.filename or "upload",
        source_type=source_type,
    )
