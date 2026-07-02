import json
import sys
from datetime import UTC, datetime
from typing import Any

import httpx
from app.core.config import settings
from app.schemas.intake import LeadDetails, StoredCall
from app.services.website_knowledge_service import website_knowledge_service


class SarvamAgentService:
    def __init__(self) -> None:
        self._cached_start_prompt: tuple[str, str] | None = None

    def get_cached_start_prompt(self) -> tuple[str, str] | None:
        return self._cached_start_prompt

    async def prewarm_start_prompt(self, caller_number: str, to_number: str) -> tuple[str, str]:
        call = StoredCall(
            id="prompt-cache",
            provider="sarvam",
            provider_call_id="prompt-cache",
            from_number=caller_number,
            to_number=to_number,
            status="in_progress",
            lead=LeadDetails(phone=caller_number, language="te-IN"),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        _lead, reply, language, _should_end = await self.start_conversation(call)
        if reply:
            self._cached_start_prompt = (reply, language)
        return reply, language

    async def start_conversation(self, call: StoredCall) -> tuple[LeadDetails, str, str, bool]:
        return await self._generate(call=call, message="CALL_STARTED", event="call_started")

    async def handle_no_speech(self, call: StoredCall) -> tuple[LeadDetails, str, str, bool]:
        return await self._generate(
            call=call,
            message="NO_CLEAR_SPEECH_DETECTED",
            event="no_speech_detected",
        )

    async def process(self, call: StoredCall, message: str) -> tuple[LeadDetails, str, str, bool]:
        return await self._generate(call=call, message=message, event="caller_message")

    async def _generate(
        self,
        call: StoredCall,
        message: str,
        event: str,
    ) -> tuple[LeadDetails, str, str, bool]:
        if "pytest" in sys.modules:
            raise RuntimeError("Sarvam is disabled during tests")
        if not settings.sarvam_api_key:
            raise RuntimeError("Sarvam API key is not configured")

        raw = await self._call_chat_completion(call, message, event)
        result = self._parse_result(raw)
        lead = self._merge_lead(call.lead, result)
        language = "te-IN"
        lead.language = language
        lead.preferred_language = lead.preferred_language or "Telugu"

        reply = str(result.get("reply") or "").strip()
        if not reply:
            reply = self._fallback_reply(lead)

        should_end = bool(result.get("should_end_call")) or lead.status in {
            "agreed",
            "not_agreed",
            "needs_team",
        }
        return lead, reply, language, should_end

    async def _call_chat_completion(self, call: StoredCall, message: str, event: str) -> str:
        body = {
            "model": settings.sarvam_chat_model,
            "temperature": 0.25,
            "max_tokens": 180,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": self._user_payload(call, message, event)},
            ],
        }
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(
                "https://api.sarvam.ai/v1/chat/completions",
                headers={
                    "api-subscription-key": settings.sarvam_api_key or "",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
        data = response.json()
        choices = data.get("choices") if isinstance(data, dict) else None
        if choices:
            message_data = choices[0].get("message", {})
            return str(message_data.get("content") or choices[0].get("text") or "")
        return str(data.get("output_text") or data.get("text") or data)

    def _user_payload(self, call: StoredCall, message: str, event: str) -> str:
        transcript = [
            {"role": turn.role, "text": turn.text, "language": turn.language}
            for turn in call.transcript[-12:]
        ]
        payload = {
            "business": "Rubi web development team",
            "event": event,
            "caller_number": call.from_number,
            "current_lead": call.lead.model_dump(),
            "latest_caller_message": message,
            "recent_transcript": transcript,
            "website_context": website_knowledge_service.answer(message),
        }
        return json.dumps(payload, ensure_ascii=False)

    def _parse_result(self, raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").removeprefix("json").strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return {"reply": cleaned}
        return parsed if isinstance(parsed, dict) else {"reply": cleaned}

    def _merge_lead(self, current: LeadDetails, result: dict[str, Any]) -> LeadDetails:
        lead = current.model_copy(deep=True)
        for field in (
            "name",
            "phone",
            "need",
            "project_type",
            "budget",
            "timeline",
            "preferred_language",
            "callback_notes",
            "status",
        ):
            value = result.get(field)
            if isinstance(value, str) and value.strip():
                setattr(lead, field, value.strip()[:500])

        agreed = result.get("agreed")
        if isinstance(agreed, bool):
            lead.agreed = agreed
        elif isinstance(agreed, str):
            lowered = agreed.strip().lower()
            if lowered in {"true", "yes", "agreed", "agree", "అవును", "సరే"}:
                lead.agreed = True
            elif lowered in {"false", "no", "not_agreed", "not agreed", "వద్దు", "కాదు"}:
                lead.agreed = False

        if lead.agreed is True:
            lead.status = "agreed"
        elif lead.agreed is False:
            lead.status = "not_agreed"
        elif lead.name and lead.need and lead.budget:
            lead.status = "qualified"
        elif not lead.status:
            lead.status = "collecting"
        return lead

    def _fallback_reply(self, lead: LeadDetails) -> str:
        if lead.status == "agreed":
            return "చాలా ధన్యవాదాలు అండి. మా రూబి టీమ్ త్వరలో మీకు తిరిగి కాల్ చేస్తుంది."
        if lead.status == "needs_team":
            return "క్షమించండి అండి, దీనిని మా టీమ్‌తో నిర్ధారించి మీకు తిరిగి కాల్ చేస్తాము."
        if not lead.name:
            return "నమస్కారం అండి. నేను రూబి. మీ పేరు చెప్పగలరా?"
        if not lead.need:
            return "మీకు వెబ్‌సైట్, ఈకామర్స్, ల్యాండింగ్ పేజ్ లేదా కస్టమ్ వెబ్ యాప్‌లో ఏది కావాలి?"
        if not lead.budget:
            return "ఈ ప్రాజెక్ట్ కోసం మీ బడ్జెట్ రేంజ్ ఎంతగా అనుకుంటున్నారు?"
        return "మీ వివరాలు నమోదు చేశాను. మా టీమ్ మీకు తిరిగి కాల్ చేయడం సరేనా?"

    def _system_prompt(self) -> str:
        lines = [
            "నువ్వు రూబి. వెబ్ డెవలప్‌మెంట్ కంపెనీకి చెందిన మర్యాదగల మహిళా వాయిస్ ఏజెంట్.",
            "ఎల్లప్పుడూ స్వచ్ఛమైన, సహజమైన, వినయపూర్వకమైన తెలుగులో మాత్రమే సమాధానం ఇవ్వాలి.",
            "ఇంగ్లీష్ లేదా టెంగ్లిష్ వాడకూడదు. కాలర్ ఇంగ్లీష్‌లో మాట్లాడినా తెలుగులోనే కొనసాగాలి.",
            "వాయిస్ కాల్ కాబట్టి ప్రతి సమాధానం చిన్నగా, స్పష్టంగా, మృదువుగా ఉండాలి.",
            "ఒక్కసారికి ఒక్క ప్రశ్న మాత్రమే అడగాలి.",
            "event call_started అయితే రూబి అని పరిచయం చేసుకుని వెబ్ డెవలప్‌మెంట్ సహాయం గురించి చెప్పి పేరు అడగాలి.",
            "event no_speech_detected అయితే వినిపించలేదని మర్యాదగా చెప్పి మళ్లీ చెప్పమని అడగాలి.",
            "సేకరించవలసిన వివరాలు: పేరు, ఫోన్, ప్రాజెక్ట్ రకం, అవసరం, బడ్జెట్, టైమ్‌లైన్, కాల్‌బ్యాక్ అంగీకారం.",
            "వెబ్‌సైట్, ఈకామర్స్, ల్యాండింగ్ పేజ్, డ్యాష్‌బోర్డ్, CRM, హోస్టింగ్, డొమైన్, SEO, పేమెంట్ ఇంటిగ్రేషన్ విషయాలు మాత్రమే మాట్లాడాలి.",
            "తెలియని లేదా వెబ్ డెవలప్‌మెంట్‌కు సంబంధం లేని ప్రశ్న అయితే టీమ్‌కి కనెక్ట్ చేస్తానని చెప్పి status needs_team చేయాలి.",
            "కస్టమర్ ఒప్పుకుంటే agreed true, status agreed చేయాలి.",
            "కస్టమర్ వద్దు అంటే agreed false, status not_agreed చేయాలి.",
            "JSON మాత్రమే ఇవ్వాలి. ఇతర టెక్స్ట్ ఇవ్వకూడదు.",
            "JSON keys: reply, language, preferred_language, name, phone, project_type,",
            "need, budget, timeline, callback_notes, agreed, status, should_end_call, summary.",
            "language ఎల్లప్పుడూ te-IN. preferred_language ఎల్లప్పుడూ Telugu.",
            "status values: collecting, qualified, agreed, not_agreed, needs_team.",
        ]
        return "\n".join(lines)


sarvam_agent_service = SarvamAgentService()
