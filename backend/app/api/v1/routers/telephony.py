from app.schemas.telephony import (
    CallSessionRead,
    InboundCallRequest,
    LanguageConfig,
    OutboundCallRequest,
    ProviderAnswerInstructions,
    RecordingUpdate,
    TranscriptTurnCreate,
)
from app.services.language_service import language_service
from app.services.storage_service import storage_service
from app.services.telephony_service import telephony_service
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/languages", response_model=LanguageConfig)
async def get_language_config() -> LanguageConfig:
    return language_service.config


@router.get("/calls", response_model=list[CallSessionRead])
async def list_phone_sessions() -> list[CallSessionRead]:
    stored_calls = storage_service.list_calls()
    if stored_calls:
        return [
            CallSessionRead(
                id=call.id,
                provider=call.provider,
                provider_call_id=call.provider_call_id,
                from_number=call.from_number,
                to_number=call.to_number,
                agent_id="agent_default",
                status=call.status,
                language=call.language,
                recording_enabled=True,
                recording_status=call.recording_status,
                recording_url=call.recording_url,
                storage_key=call.recording_sid,
                transcript=[],
                started_at=call.created_at,
            )
            for call in stored_calls
        ]
    return await telephony_service.list_sessions()


@router.post("/inbound", response_model=ProviderAnswerInstructions, status_code=202)
async def receive_inbound_call(payload: InboundCallRequest) -> ProviderAnswerInstructions:
    return await telephony_service.receive_inbound_call(payload)


@router.post("/outbound", response_model=CallSessionRead, status_code=202)
async def start_outbound_call(payload: OutboundCallRequest) -> CallSessionRead:
    return await telephony_service.start_outbound_call(payload)


@router.post("/calls/{call_id}/answer", response_model=ProviderAnswerInstructions)
async def answer_call(call_id: str) -> ProviderAnswerInstructions:
    try:
        return await telephony_service.answer_call(call_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Call not found") from exc


@router.post("/calls/{call_id}/transcript", response_model=CallSessionRead)
async def append_transcript(call_id: str, payload: TranscriptTurnCreate) -> CallSessionRead:
    try:
        return await telephony_service.append_transcript(call_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Call not found") from exc


@router.post("/calls/{call_id}/recording", response_model=CallSessionRead)
async def update_recording(call_id: str, payload: RecordingUpdate) -> CallSessionRead:
    try:
        return await telephony_service.update_recording(call_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Call not found") from exc


@router.post("/calls/{call_id}/end", response_model=CallSessionRead)
async def end_call(call_id: str) -> CallSessionRead:
    try:
        return await telephony_service.end_call(call_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Call not found") from exc
