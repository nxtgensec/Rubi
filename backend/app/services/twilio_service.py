from html import escape
from urllib.parse import urljoin

import httpx
from app.core.config import settings
from app.schemas.intake import LeadDetails, StoredCall
from app.schemas.telephony import InboundCallRequest, OutboundCallRequest, RecordingUpdate
from app.services.intake_agent_service import intake_agent_service
from app.services.storage_service import storage_service
from app.services.telephony_service import telephony_service


class TwilioConfigurationError(RuntimeError):
    pass


class TwilioService:
    async def handle_inbound_webhook(self, form: dict[str, str]) -> str:
        instructions = await telephony_service.receive_inbound_call(
            InboundCallRequest(
                provider="twilio",
                provider_call_id=form.get("CallSid", "unknown"),
                from_number=form.get("From", "unknown"),
                to_number=form.get("To", settings.twilio_phone_number or "unknown"),
                preferred_language=form.get("SpeechResultLanguage"),
            )
        )
        storage_service.upsert_call(
            StoredCall(
                id=instructions.call_id,
                provider="twilio",
                provider_call_id=form.get("CallSid", "unknown"),
                from_number=form.get("From", "unknown"),
                to_number=form.get("To", settings.twilio_phone_number or "unknown"),
                status="in_progress",
                language=instructions.language,
                lead=LeadDetails(
                    phone=form.get("From", "unknown"),
                    language=instructions.language,
                ),
                created_at=telephony_service.get_started_at(instructions.call_id),
                updated_at=telephony_service.get_started_at(instructions.call_id),
            )
        )
        await self._start_twilio_recording(
            provider_call_id=form.get("CallSid", ""),
            call_id=instructions.call_id,
        )
        return self._build_voice_twiml(
            call_id=instructions.call_id,
            greeting=instructions.greeting,
            language=instructions.language,
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

    async def handle_gather(self, call_id: str, form: dict[str, str]) -> str:
        call = storage_service.get_call(call_id)
        if not call:
            return self._simple_twiml("Sorry, I could not find this call session.")

        speech_result = form.get("SpeechResult", "").strip()
        if not speech_result:
            return self._continue_gather_twiml(
                call_id=call_id,
                prompt=(
                    "Sorry, clear ga vinipinchaledu. Mee peru, web development requirement, "
                    "budget cheppagalara?"
                ),
                language=call.language,
            )

        response = intake_agent_service.process_caller_message(
            call_id=call_id,
            message=speech_result,
            from_number=call.from_number,
        )
        call = storage_service.get_call(call_id)
        if call and call.lead.status in {"agreed", "not_agreed", "needs_team"}:
            return self._simple_twiml(response)
        return self._continue_gather_twiml(call_id=call_id, prompt=response, language=call.language)

    async def start_outbound_call(self, payload: OutboundCallRequest) -> str:
        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            raise TwilioConfigurationError("Twilio credentials are not configured")

        session = await telephony_service.start_outbound_call(
            payload.model_copy(update={"provider": "twilio"})
        )
        voice_url = urljoin(settings.public_backend_url, "/api/v1/twilio/voice")
        status_url = urljoin(settings.public_backend_url, "/api/v1/twilio/status")

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

    async def _start_twilio_recording(self, provider_call_id: str, call_id: str) -> None:
        if (
            not provider_call_id
            or not settings.twilio_account_sid
            or not settings.twilio_auth_token
        ):
            return
        recording_callback = self._recording_callback_url(call_id)
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

    def _build_voice_twiml(self, call_id: str, greeting: str, language: str) -> str:
        prompt = (
            "Namaskaram, nenu Rubi nundi maatladutunna. "
            "Mee web development project kosam help cheyyadaniki call chestunna. "
            "Mee peru, meeku website aa ecommerce aa custom web app aa, "
            "mariyu mee budget range cheppandi. Meeru Telugu, English, "
            "leda Tenglish lo maatladachu."
        )
        return self._continue_gather_twiml(call_id=call_id, prompt=prompt, language=language)

    def _continue_gather_twiml(self, call_id: str, prompt: str, language: str) -> str:
        gather_url = (
            f"{settings.public_backend_url.rstrip('/')}/api/v1/twilio/gather"
            f"?call_id={call_id}"
        )
        say_language = self._twilio_say_language(language)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Gather input="speech" action="{escape(gather_url)}" method="POST" '
            f'language="{say_language}" speechTimeout="auto" timeout="6">'
            f'<Say language="{say_language}" voice="{self._twilio_say_voice(language)}">'
            f"{escape(prompt)}</Say>"
            "</Gather>"
            f'<Say language="{say_language}" voice="{self._twilio_say_voice(language)}">'
            "Response receive avvaledu. Thank you.</Say>"
            "</Response>"
        )

    def _simple_twiml(self, message: str) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response>"
            f'<Say language="en-IN" voice="{self._twilio_say_voice("tenglish")}">'
            f"{escape(message)}</Say>"
            "</Response>"
        )

    def _recording_callback_url(self, call_id: str) -> str:
        return (
            f"{settings.public_backend_url.rstrip('/')}/api/v1/twilio/recording"
            f"?call_id={escape(call_id)}"
        )

    def _twilio_say_language(self, language: str) -> str:
        # Twilio <Say> language support is provider-specific; use Indian English as fallback.
        supported = {
            "en-IN": "en-IN",
            "hi-IN": "hi-IN",
        }
        return supported.get(language, "en-IN")

    def _twilio_say_voice(self, language: str) -> str:
        return "Polly.Aditi"


twilio_service = TwilioService()
