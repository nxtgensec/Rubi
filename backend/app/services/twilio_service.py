import asyncio
import os
from html import escape
from urllib.parse import urlencode

import httpx
from app.core.config import settings
from app.schemas.intake import LeadDetails, StoredCall
from app.schemas.telephony import InboundCallRequest, OutboundCallRequest, RecordingUpdate
from app.services.intake_agent_service import intake_agent_service
from app.services.sarvam_agent_service import sarvam_agent_service
from app.services.sarvam_tts_service import sarvam_tts_service
from app.services.storage_service import storage_service
from app.services.telephony_service import telephony_service


class TwilioConfigurationError(RuntimeError):
    pass


class TwilioService:
    async def handle_inbound_webhook(
        self,
        form: dict[str, str],
        callback_base_url: str | None = None,
    ) -> str:
        instructions = await telephony_service.receive_inbound_call(
            InboundCallRequest(
                provider="twilio",
                provider_call_id=form.get("CallSid", "unknown"),
                from_number=form.get("OutboundTo") or form.get("From", "unknown"),
                to_number=(
                    form.get("OutboundFrom")
                    or form.get("To", settings.twilio_phone_number or "unknown")
                ),
                preferred_language=form.get("SpeechResultLanguage"),
            )
        )
        storage_service.upsert_call(
            StoredCall(
                id=instructions.call_id,
                provider="twilio",
                provider_call_id=form.get("CallSid", "unknown"),
                from_number=form.get("OutboundTo") or form.get("From", "unknown"),
                to_number=(
                    form.get("OutboundFrom")
                    or form.get("To", settings.twilio_phone_number or "unknown")
                ),
                status="in_progress",
                language=instructions.language,
                lead=LeadDetails(
                    phone=form.get("OutboundTo") or form.get("From", "unknown"),
                    language=instructions.language,
                ),
                created_at=telephony_service.get_started_at(instructions.call_id),
                updated_at=telephony_service.get_started_at(instructions.call_id),
            )
        )
        cached_prompt = sarvam_agent_service.get_cached_start_prompt()
        prompt, prompt_language = (
            (form.get("Prompt"), form.get("PromptLanguage") or instructions.language)
            if form.get("Prompt")
            else cached_prompt
        ) or (
            self._fallback_initial_prompt(),
            instructions.language,
        )
        storage_service.append_transcript(
            instructions.call_id,
            "assistant",
            prompt,
            prompt_language,
        )
        asyncio.create_task(
            self._start_twilio_recording(
                provider_call_id=form.get("CallSid", ""),
                call_id=instructions.call_id,
                callback_base_url=callback_base_url,
            )
        )
        return self._build_voice_twiml(
            call_id=instructions.call_id,
            prompt=prompt,
            language=prompt_language,
            callback_base_url=callback_base_url,
        )

    async def handle_recording_callback(self, form: dict[str, str]) -> None:
        call_id = form.get("CallId") or form.get("call_id")
        if not call_id:
            return
        recording_url = form.get("RecordingUrl")
        await telephony_service.update_recording(
            call_id,
            RecordingUpdate(
                recording_url=recording_url,
                storage_key=form.get("RecordingSid"),
                status=form.get("RecordingStatus", "available"),
            ),
        )
        try:
            storage_service.update_recording(
                call_id=call_id,
                recording_status=form.get("RecordingStatus", "available"),
                recording_url=recording_url,
                recording_sid=form.get("RecordingSid"),
            )
        except KeyError:
            return

    async def handle_gather(
        self,
        call_id: str,
        form: dict[str, str],
        callback_base_url: str | None = None,
    ) -> str:
        call = storage_service.get_call(call_id)
        if not call:
            return self._simple_twiml(
                "క్షమించండి, ఈ కాల్ వివరాలు కనిపించలేదు. ధన్యవాదాలు.",
                callback_base_url=callback_base_url,
            )

        speech_result = form.get("SpeechResult", "").strip()
        if not speech_result:
            prompt, language = await self._no_speech_prompt_from_sarvam(call)
            return self._continue_gather_twiml(
                call_id=call_id,
                prompt=prompt,
                language=language,
                callback_base_url=callback_base_url,
            )

        response = await intake_agent_service.process_caller_message(
            call_id=call_id,
            message=speech_result,
            from_number=call.from_number,
        )
        call = storage_service.get_call(call_id)
        if call and call.lead.status in {"agreed", "not_agreed", "needs_team"}:
            return self._simple_twiml(response, callback_base_url=callback_base_url)
        return self._continue_gather_twiml(
            call_id=call_id,
            prompt=response,
            language=call.language,
            callback_base_url=callback_base_url,
        )

    async def start_outbound_call(
        self,
        payload: OutboundCallRequest,
        callback_base_url: str | None = None,
    ) -> str:
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            raise TwilioConfigurationError("Twilio credentials are not configured")

        session = await telephony_service.start_outbound_call(
            payload.model_copy(update={"provider": "twilio"})
        )
        prompt_query: dict[str, str] = {}
        try:
            prompt, prompt_language = await sarvam_agent_service.prewarm_start_prompt(
                caller_number=payload.to_number,
                to_number=settings.twilio_phone_number or payload.from_number,
            )
            prompt_query = {
                "Prompt": prompt,
                "PromptLanguage": prompt_language,
            }
        except (RuntimeError, httpx.HTTPError, ValueError, KeyError):
            pass
        voice_url = self._backend_url("/api/v1/twilio/voice", callback_base_url=callback_base_url)
        outbound_from = settings.twilio_phone_number or payload.from_number
        query = urlencode(
            {
                "OutboundTo": payload.to_number,
                "OutboundFrom": outbound_from,
                **prompt_query,
            },
        )
        voice_url = f"{voice_url}?{query}"
        status_url = self._backend_url("/api/v1/twilio/status", callback_base_url=callback_base_url)

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{settings.twilio_account_sid}/Calls.json",
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data={
                    "To": payload.to_number,
                    "From": settings.twilio_phone_number or payload.from_number,
                    "Url": voice_url,
                    "Method": "POST",
                    "StatusCallback": status_url,
                    "StatusCallbackMethod": "POST",
                    "StatusCallbackEvent": ["initiated", "ringing", "answered", "completed"],
                },
            )
            response.raise_for_status()
            data = response.json()

        return data["sid"] if "sid" in data else session.provider_call_id

    async def _start_twilio_recording(
        self,
        provider_call_id: str,
        call_id: str,
        callback_base_url: str | None = None,
    ) -> None:
        if (
            not provider_call_id
            or not settings.twilio_account_sid
            or not settings.twilio_auth_token
        ):
            return
        recording_callback = self._recording_callback_url(
            call_id,
            callback_base_url=callback_base_url,
        )
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/"
                    f"{settings.twilio_account_sid}/Calls/{provider_call_id}/Recordings.json",
                    auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                    data={
                        "RecordingStatusCallback": recording_callback,
                        "RecordingStatusCallbackMethod": "POST",
                        "RecordingChannels": "dual",
                    },
                )
        except httpx.HTTPError:
            return

    def _build_voice_twiml(
        self,
        call_id: str,
        prompt: str,
        language: str,
        callback_base_url: str | None = None,
    ) -> str:
        return self._continue_gather_twiml(
            call_id=call_id,
            prompt=prompt,
            language=language,
            callback_base_url=callback_base_url,
        )

    async def _initial_prompt_from_sarvam(self, call_id: str) -> str:
        call = storage_service.get_call(call_id)
        if not call:
            return self._fallback_initial_prompt()
        try:
            lead, prompt, language, _should_end = await sarvam_agent_service.start_conversation(
                call,
            )
            storage_service.update_lead(call_id, lead)
            call = storage_service.get_call(call_id)
            if call:
                call.language = language
                storage_service.upsert_call(call)
            storage_service.append_transcript(call_id, "assistant", prompt, language)
            return prompt
        except (RuntimeError, httpx.HTTPError, ValueError, KeyError):
            prompt = self._fallback_initial_prompt()
            storage_service.append_transcript(call_id, "assistant", prompt, call.language)
            return prompt

    async def _no_speech_prompt_from_sarvam(self, call: StoredCall) -> tuple[str, str]:
        try:
            lead, prompt, language, _should_end = await sarvam_agent_service.handle_no_speech(call)
            storage_service.update_lead(call.id, lead)
            stored_call = storage_service.get_call(call.id)
            if stored_call:
                stored_call.language = language
                storage_service.upsert_call(stored_call)
            storage_service.append_transcript(call.id, "assistant", prompt, language)
            return prompt, language
        except (RuntimeError, httpx.HTTPError, ValueError, KeyError):
            prompt = "క్షమించండి అండి, స్పష్టంగా వినిపించలేదు. దయచేసి మళ్లీ చెప్పగలరా?"
            storage_service.append_transcript(call.id, "assistant", prompt, call.language)
            return prompt, call.language

    def _fallback_initial_prompt(self) -> str:
        return sarvam_agent_service.initial_greeting()

    def _continue_gather_twiml(
        self,
        call_id: str,
        prompt: str,
        language: str,
        callback_base_url: str | None = None,
    ) -> str:
        gather_url = (
            f"{self._backend_url('/api/v1/twilio/gather', callback_base_url=callback_base_url)}"
            f"?call_id={call_id}"
        )
        gather_language = self._twilio_gather_language(language)
        say_language = self._twilio_say_language(language)
        no_response_twiml = self._voice_twiml(
            "క్షమించండి, స్పందన రాలేదు. ధన్యవాదాలు.",
            say_language,
            language,
            callback_base_url,
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Gather input="speech" action="{escape(gather_url)}" method="POST" '
            f'language="{gather_language}" speechTimeout="2" timeout="4" '
            'actionOnEmptyResult="true">'
            f"{self._voice_twiml(prompt, say_language, language, callback_base_url)}"
            "</Gather>"
            f"{no_response_twiml}"
            "</Response>"
        )

    def _simple_twiml(self, message: str, callback_base_url: str | None = None) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f"{self._voice_twiml(message, 'en-IN', 'te-IN', callback_base_url)}"
            "</Response>"
        )

    def _recording_callback_url(
        self,
        call_id: str,
        callback_base_url: str | None = None,
    ) -> str:
        return (
            f"{self._backend_url('/api/v1/twilio/recording', callback_base_url=callback_base_url)}"
            f"?call_id={escape(call_id)}"
        )

    def _backend_url(self, path: str, callback_base_url: str | None = None) -> str:
        base_url = (
            callback_base_url
            or os.getenv("PUBLIC_BACKEND_URL")
            or settings.public_backend_url
        )
        base_url = base_url.rstrip("/")
        if os.getenv("VERCEL") and "/_/backend" not in base_url:
            base_url = f"{base_url}/_/backend"
        return f"{base_url}/{path.lstrip('/')}"

    def _twilio_say_language(self, language: str) -> str:
        # Twilio <Say> language support is provider-specific; use Indian English as fallback.
        supported = {
            "en-IN": "en-IN",
            "hi-IN": "hi-IN",
        }
        return supported.get(language, "en-IN")

    def _twilio_say_voice(self, language: str) -> str:
        return "Polly.Aditi"

    def _twilio_gather_language(self, language: str) -> str:
        supported = {
            "te-IN": "te-IN",
            "en-IN": "en-IN",
            "hi-IN": "hi-IN",
        }
        return supported.get(language, "en-IN")

    def _voice_twiml(
        self,
        text: str,
        say_language: str,
        language: str,
        callback_base_url: str | None,
    ) -> str:
        if language == "te-IN" and sarvam_tts_service.enabled():
            audio_url = sarvam_tts_service.audio_url(text, callback_base_url=callback_base_url)
            return f"<Play>{escape(audio_url)}</Play>"
        return (
            f'<Say language="{say_language}" voice="{self._twilio_say_voice(language)}">'
            f"{escape(text)}</Say>"
        )


twilio_service = TwilioService()
