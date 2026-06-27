from enum import StrEnum


class EventType(StrEnum):
    CALL_STARTED = "CallStarted"
    CALL_ENDED = "CallEnded"
    TRANSCRIPT_RECEIVED = "TranscriptReceived"
    USER_INTERRUPTED = "UserInterrupted"
    LLM_STARTED = "LLMStarted"
    LLM_COMPLETED = "LLMCompleted"
    TOOL_STARTED = "ToolStarted"
    TOOL_COMPLETED = "ToolCompleted"
    TTS_STARTED = "TTSStarted"
    TTS_COMPLETED = "TTSCompleted"
    MEMORY_UPDATED = "MemoryUpdated"
