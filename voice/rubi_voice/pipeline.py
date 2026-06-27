from dataclasses import dataclass


@dataclass(slots=True)
class VoicePipelineConfig:
    vad_enabled: bool = True
    interruption_enabled: bool = True
    stt_provider: str = "faster-whisper"
    tts_provider: str = "piper"
    language: str = "te-IN"


class VoicePipeline:
    def __init__(self, config: VoicePipelineConfig) -> None:
        self.config = config

    async def start(self) -> None:
        """Start the browser or LiveKit voice pipeline."""

    async def stop(self) -> None:
        """Stop voice streaming and release provider resources."""
