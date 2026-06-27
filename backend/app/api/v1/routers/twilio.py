from app.schemas.telephony import OutboundCallRequest
from app.services.twilio_service import TwilioConfigurationError, twilio_service
from fastapi import APIRouter, Form, HTTPException, Request, Response

router = APIRouter()


@router.post("/voice")
async def voice_webhook(request: Request) -> Response:
    form = {key: value for key, value in (await request.form()).items() if isinstance(value, str)}
    twiml = await twilio_service.handle_inbound_webhook(form)
    return Response(content=twiml, media_type="application/xml")


@router.post("/recording")
async def recording_callback(request: Request, call_id: str | None = None) -> dict[str, str]:
    form = {key: value for key, value in (await request.form()).items() if isinstance(value, str)}
    if call_id:
        form["call_id"] = call_id
    await twilio_service.handle_recording_callback(form)
    return {"status": "ok"}


@router.post("/gather")
async def gather_callback(request: Request, call_id: str) -> Response:
    form = {key: value for key, value in (await request.form()).items() if isinstance(value, str)}
    twiml = await twilio_service.handle_gather(call_id, form)
    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def status_callback(
    call_id: str | None = None,
    call_status: str | None = Form(default=None, alias="CallStatus"),
) -> dict[str, str | None]:
    return {"status": "ok", "call_id": call_id, "call_status": call_status}


@router.post("/outbound")
async def outbound_call(payload: OutboundCallRequest) -> dict[str, str]:
    try:
        provider_call_id = await twilio_service.start_outbound_call(payload)
    except TwilioConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "queued", "provider_call_id": provider_call_id}
