from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import settings
from app.events.bus import Event, event_bus
from app.events.types import EventType
from app.schemas.telephony import (
    CallSessionRead,
    InboundCallRequest,
    OutboundCallRequest,
    ProviderAnswerInstructions,
    RecordingUpdate,
    TranscriptTurnCreate,
)
from app.services.language_service import language_service


class TelephonyService:
    def __init__(self) -> None:
        self._sessions: dict[str, CallSessionRead] = {}

    async def list_sessions(self) -> list[CallSessionRead]:
        return sorted(self._sessions.values(), key=lambda session: session.started_at, reverse=True)

    async def get_session(self, call_id: str) -> CallSessionRead:
        return self._sessions[call_id]

    def get_started_at(self, call_id: str):
        return self._sessions[call_id].started_at

    async def receive_inbound_call(self, payload: InboundCallRequest) -> ProviderAnswerInstructions:
        call_id = str(uuid4())
        language = language_service.resolve_language(payload.preferred_language)
        session = CallSessionRead(
            id=call_id,
            provider=payload.provider,
            provider_call_id=payload.provider_call_id,
            from_number=payload.from_number,
            to_number=payload.to_number,
            agent_id=payload.agent_id,
            status="ringing",
            language=language,
            recording_enabled=True,
            recording_status="requested",
            started_at=datetime.now(UTC),
        )
        self._sessions[call_id] = session
        await event_bus.publish(
            Event(
                type=EventType.CALL_STARTED,
                payload={
                    "call_id": call_id,
                    "from_number": payload.from_number,
                    "language": language,
                },
            )
        )
        return self._answer_instructions(session)

    async def start_outbound_call(self, payload: OutboundCallRequest) -> CallSessionRead:
        provider_call_id = f"out_{uuid4()}"
        language = language_service.resolve_language(payload.preferred_language)
        session = CallSessionRead(
            id=str(uuid4()),
            provider=payload.provider,
            provider_call_id=provider_call_id,
            from_number=payload.from_number,
            to_number=payload.to_number,
            agent_id=payload.agent_id,
            status="dialing",
            language=language,
            recording_enabled=True,
            recording_status="requested",
            started_at=datetime.now(UTC),
        )
        self._sessions[session.id] = session
        return session

    async def answer_call(self, call_id: str) -> ProviderAnswerInstructions:
        session = self._sessions[call_id]
        updated = session.model_copy(
            update={"status": "in_progress", "answered_at": datetime.now(UTC)}
        )
        self._sessions[call_id] = updated
        return self._answer_instructions(updated)

    async def append_transcript(self, call_id: str, turn: TranscriptTurnCreate) -> CallSessionRead:
        session = self._sessions[call_id]
        language = language_service.resolve_language(turn.language, turn.text)
        updated_turn = turn.model_copy(update={"language": language})
        updated = session.model_copy(
            update={
                "language": language,
                "transcript": [*session.transcript, updated_turn],
            }
        )
        self._sessions[call_id] = updated
        await event_bus.publish(
            Event(
                type=EventType.TRANSCRIPT_RECEIVED,
                payload={"call_id": call_id, "role": turn.role, "language": language},
            )
        )
        return updated

    async def update_recording(self, call_id: str, payload: RecordingUpdate) -> CallSessionRead:
        session = self._sessions[call_id]
        updated = session.model_copy(
            update={
                "recording_status": payload.status,
                "recording_url": payload.recording_url,
                "storage_key": payload.storage_key,
            }
        )
        self._sessions[call_id] = updated
        return updated

    async def end_call(self, call_id: str) -> CallSessionRead:
        session = self._sessions[call_id]
        updated = session.model_copy(update={"status": "completed", "ended_at": datetime.now(UTC)})
        self._sessions[call_id] = updated
        await event_bus.publish(Event(type=EventType.CALL_ENDED, payload={"call_id": call_id}))
        return updated

    def _answer_instructions(self, session: CallSessionRead) -> ProviderAnswerInstructions:
        greeting = {
            "te-IN": "Namaskaram, Rubi maatladutondi. Mee kosam ela sahayam cheyyali?",
            "hi-IN": "Namaste, Rubi bol rahi hoon. Main aapki kaise madad kar sakti hoon?",
            "en-IN": "Hello, this is Rubi. How can I help you today?",
            "ta-IN": "Vanakkam, Rubi pesugiren. Eppadi udhava vendum?",
            "kn-IN": "Namaskara, Rubi mathaduttide. Nimage hege sahaya madali?",
            "ml-IN": "Namaskaram, Rubi samsarikkunnu. Enthu sahayam venam?",
        }.get(session.language, "Hello, this is Rubi. How can I help you today?")
        return ProviderAnswerInstructions(
            call_id=session.id,
            stream_url=f"{settings.public_voice_stream_base_url}/{session.id}",
            recording_enabled=session.recording_enabled,
            language=session.language,
            greeting=greeting,
        )


telephony_service = TelephonyService()
