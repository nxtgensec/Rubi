from datetime import datetime

from pydantic import BaseModel, Field


class CallRead(BaseModel):
    id: str
    caller: str
    language: str = "te-IN"
    agent_id: str
    duration_seconds: int
    status: str
    recording_status: str = "available"
    recording_url: str | None = None
    summary: str
    transcript: list[str] = Field(default_factory=list)
    sentiment: str
    started_at: datetime
