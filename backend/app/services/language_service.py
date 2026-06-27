from app.schemas.telephony import LanguageConfig


class LanguageService:
    def __init__(self, config: LanguageConfig | None = None) -> None:
        self.config = config or LanguageConfig()

    def resolve_language(
        self,
        preferred_language: str | None,
        sample_text: str | None = None,
    ) -> str:
        if preferred_language in self.config.supported_languages:
            return preferred_language
        if self.config.auto_detect and sample_text:
            detected = self.detect_language(sample_text)
            if detected in self.config.supported_languages:
                return detected
        return self.config.default_language

    def detect_language(self, text: str) -> str:
        # Lightweight placeholder until Faster Whisper language detection is wired in.
        telugu_range = range(0x0C00, 0x0C7F + 1)
        devanagari_range = range(0x0900, 0x097F + 1)
        tamil_range = range(0x0B80, 0x0BFF + 1)
        kannada_range = range(0x0C80, 0x0CFF + 1)
        malayalam_range = range(0x0D00, 0x0D7F + 1)

        codepoints = [ord(character) for character in text]
        if any(codepoint in telugu_range for codepoint in codepoints):
            return "te-IN"
        if any(codepoint in devanagari_range for codepoint in codepoints):
            return "hi-IN"
        if any(codepoint in tamil_range for codepoint in codepoints):
            return "ta-IN"
        if any(codepoint in kannada_range for codepoint in codepoints):
            return "kn-IN"
        if any(codepoint in malayalam_range for codepoint in codepoints):
            return "ml-IN"
        return self.config.fallback_language


language_service = LanguageService()
