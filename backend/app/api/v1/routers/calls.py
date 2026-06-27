import httpx
from app.core.config import settings
from app.schemas.call import CallRead
from app.services.call_service import call_service
from app.services.storage_service import storage_service
from fastapi import APIRouter, HTTPException, Response

router = APIRouter()


@router.get("", response_model=list[CallRead])
async def list_calls() -> list[CallRead]:
    return await call_service.list_calls()


@router.get("/{call_id}")
async def get_call(call_id: str):
    call = storage_service.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@router.get("/{call_id}/recording")
async def get_recording(call_id: str) -> Response:
    call = storage_service.get_call(call_id)
    if not call or not call.recording_url:
        raise HTTPException(status_code=404, detail="Recording not found")
    recording_url = _recording_media_url(call.recording_url)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                recording_url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token)
                if "twilio.com" in recording_url
                and settings.twilio_account_sid
                and settings.twilio_auth_token
                else None,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not fetch recording") from exc
    media_type = response.headers.get("content-type", "audio/mpeg")
    return Response(content=response.content, media_type=media_type)


def _recording_media_url(recording_url: str) -> str:
    if "twilio.com" not in recording_url:
        return recording_url
    if recording_url.endswith((".mp3", ".wav")):
        return recording_url
    return f"{recording_url}.mp3"
