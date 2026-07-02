import base64
import hashlib
import hmac
import sys
from urllib.parse import urlencode

import httpx
from app.core.config import settings


class SarvamTTSService:
    def enabled(self) -> bool:
        return bool(settings.sarvam_api_key and "pytest" not in sys.modules)

    def audio_url(self, text: str, callback_base_url: str | None = None) -> str:
        base_url = (callback_base_url or settings.public_backend_url).rstrip("/")
        query = urlencode({"text": text, "sig": self._signature(text)})
        return f"{base_url}/api/v1/twilio/tts?{query}"

    async def synthesize(self, text: str, signature: str) -> bytes:
        if not hmac.compare_digest(signature, self._signature(text)):
            raise PermissionError("Invalid TTS signature")
        if not settings.sarvam_api_key:
            raise RuntimeError("Sarvam API key is not configured")

        body = {
            "inputs": [text[:500]],
            "target_language_code": "te-IN",
            "speaker": settings.sarvam_tts_speaker,
            "model": settings.sarvam_tts_model,
            "speech_sample_rate": 16000,
        }
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={
                    "api-subscription-key": settings.sarvam_api_key,
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
        data = response.json()
        audio = ""
        if isinstance(data, dict):
            audios = data.get("audios")
            if isinstance(audios, list) and audios:
                audio = str(audios[0])
            else:
                audio = str(data.get("audio") or data.get("audio_base64") or "")
        if not audio:
            raise RuntimeError("Sarvam TTS did not return audio")
        return base64.b64decode(audio)

    def _signature(self, text: str) -> str:
        secret = settings.jwt_secret.encode("utf-8")
        digest = hmac.new(secret, text.encode("utf-8"), hashlib.sha256).hexdigest()
        return digest[:32]


sarvam_tts_service = SarvamTTSService()
