import json

from app.schemas.telephony import TranscriptTurnCreate
from app.services.telephony_service import telephony_service
from fastapi import WebSocket


class MediaStreamService:
    async def handle_twilio_stream(self, call_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        while True:
            message = await websocket.receive_text()
            event = json.loads(message)
            event_type = event.get("event")
            if event_type == "start":
                await telephony_service.answer_call(call_id)
            if event_type == "media":
                # Twilio sends base64 mu-law audio here. Faster Whisper integration will consume it.
                continue
            if event_type == "stop":
                await telephony_service.end_call(call_id)
                break

    async def append_demo_transcript(self, call_id: str, text: str) -> None:
        await telephony_service.append_transcript(
            call_id,
            TranscriptTurnCreate(role="user", text=text),
        )


media_stream_service = MediaStreamService()
