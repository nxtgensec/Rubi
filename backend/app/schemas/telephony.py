from datetime import datetime

from pydantic import BaseModel, Field


class LanguageConfig(BaseModel):
    default_language: str = "te-IN"
    fallback_language: str = "en-IN"
    supported_languages: list[str] = Field(
        default_factory=lambda: ["te-IN", "en-IN", "hi-IN", "ta-IN", "kn-IN", "ml-IN"],
    )
    auto_detect: bool = True


class InboundCallRequest(BaseModel):
    provider: str = "generic"
    provider_call_id: str
    from_number: str
    to_number: str
    agent_id: str = "agent_default"
    preferred_language: str | None = None


class OutboundCallRequest(BaseModel):
    provider: str = "generic"
    to_number: str
    from_number: str
    agent_id: str = "agent_default"
    preferred_language: str | None = None


class TranscriptTurnCreate(BaseModel):
    role: str
    text: str
    language: str | None = None
    confidence: float | None = None


class RecordingUpdate(BaseModel):
    recording_url: str | None = None
    storage_key: str | None = None
    status: str = "available"


class CallSessionRead(BaseModel):
    id: str
    provider: str
    provider_call_id: str
    from_number: str
    to_number: str
    agent_id: str
    status: str
    language: str
    recording_enabled: bool
    recording_status: str
    recording_url: str | None = None
    storage_key: str | None = None
    transcript: list[TranscriptTurnCreate] = Field(default_factory=list)
    started_at: datetime
    answered_at: datetime | None = None
    ended_at: datetime | None = None


class ProviderAnswerInstructions(BaseModel):
    call_id: str
    action: str = "answer"
    stream_url: str
    recording_enabled: bool = True
    language: str
    greeting: str
