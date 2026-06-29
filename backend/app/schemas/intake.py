from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LeadDetails(BaseModel):
    name: str | None = None
    phone: str | None = None
    need: str | None = None
    project_type: str | None = None
    budget: str | None = None
    timeline: str | None = None
    preferred_language: str | None = None
    callback_notes: str | None = None
    language: str = "te-IN"
    agreed: bool | None = None
    status: str = "collecting"


class StoredTranscriptTurn(BaseModel):
    role: str
    text: str
    language: str = "en-IN"
    created_at: datetime


class StoredCall(BaseModel):
    id: str
    provider: str
    provider_call_id: str
    from_number: str
    to_number: str
    status: str
    language: str = "te-IN"
    recording_status: str = "requested"
    recording_url: str | None = None
    recording_sid: str | None = None
    lead: LeadDetails = Field(default_factory=LeadDetails)
    transcript: list[StoredTranscriptTurn] = Field(default_factory=list)
    summary: str = "No conversation captured yet."
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
