from app.schemas.tool import ToolRead
from fastapi import APIRouter

router = APIRouter()


@router.get("", response_model=list[ToolRead])
async def list_tools() -> list[ToolRead]:
    return [
        ToolRead(name="book_appointment", description="Book an appointment on a calendar."),
        ToolRead(name="send_email", description="Send a transactional email."),
        ToolRead(name="send_whatsapp", description="Send a WhatsApp message through a provider."),
        ToolRead(name="create_lead", description="Create or update a CRM lead."),
    ]
