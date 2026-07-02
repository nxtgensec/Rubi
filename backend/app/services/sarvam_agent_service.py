import json
import re
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
        lead = call.lead.model_copy(deep=True)
        lead.language = "te-IN"
        lead.preferred_language = lead.preferred_language or "Telugu"
        lead.status = lead.status or "collecting"
        return lead, self.initial_greeting(), "te-IN", False

    def initial_greeting(self) -> str:
        return (
            "హలో అండి, నేను రూబికార్న్ టెక్నాలజీస్ నుండి కావిత మాట్లాడుతున్నాను. "
            "మీకు ఏ డెవలప్‌మెంట్ సహాయం కావాలి?"
        )

    async def handle_no_speech(self, call: StoredCall) -> tuple[LeadDetails, str, str, bool]:
        return await self._generate(
            call=call,
            message="NO_CLEAR_SPEECH_DETECTED",
            event="no_speech_detected",
        )

    async def process(self, call: StoredCall, message: str) -> tuple[LeadDetails, str, str, bool]:
        return await self._generate(call=call, message=message, event="caller_message")

    def try_fast_response(
        self,
        call: StoredCall,
        message: str,
    ) -> tuple[LeadDetails, str, str, bool] | None:
        if not self._has_fast_development_signal(message):
            return None
        lead = self._hydrate_development_need(call.lead.model_copy(deep=True), message)
        lead.language = "te-IN"
        lead.preferred_language = lead.preferred_language or "Telugu"
        reply = self._development_reply(lead, message)
        should_end = lead.status in {"agreed", "not_agreed", "needs_team"}
        return lead, reply, "te-IN", should_end

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
        if event == "caller_message":
            lead = self._hydrate_development_need(lead, message)
        language = "te-IN"
        lead.language = language
        lead.preferred_language = lead.preferred_language or "Telugu"

        reply = str(result.get("reply") or "").strip()
        if event == "caller_message" and (not reply or self._is_repeated_intro(reply)):
            reply = self._development_reply(lead, message)
        elif not reply:
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
            "max_tokens": 120,
            "messages": [
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": self._user_payload(call, message, event)},
            ],
        }
        async with httpx.AsyncClient(timeout=5) as client:
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
            "business": "Rubicorn Technologies web development team",
            "event": event,
            "event_instruction": self._event_instruction(event),
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

    def _has_fast_development_signal(self, message: str) -> bool:
        lowered = message.lower()
        return any(term in lowered for term in self._development_terms())

    def _development_terms(self) -> tuple[str, ...]:
        return (
            "website",
            "web site",
            "ecommerce",
            "e-commerce",
            "payment",
            "admin",
            "dashboard",
            "crm",
            "app",
            "application",
            "api",
            "database",
            "booking",
            "automation",
            "chatbot",
            "seo",
            "hosting",
            "domain",
            "landing",
            "redesign",
            "maintenance",
            "budget",
            "cost",
            "price",
            "timeline",
            "time",
        )

    def _hydrate_development_need(self, lead: LeadDetails, message: str) -> LeadDetails:
        lowered = message.lower()
        if not lead.name:
            name = self._extract_name(message)
            if name:
                lead.name = name
        if not lead.budget:
            budget = self._extract_budget(message)
            if budget:
                lead.budget = budget
        agreement = self._extract_agreement(message)
        if agreement is not None:
            lead.agreed = agreement
        if not lead.need and any(term in lowered for term in self._development_terms()):
            lead.need = message.strip()[:240]
        if not lead.project_type:
            if "ecommerce" in lowered or "e-commerce" in lowered:
                lead.project_type = "Ecommerce website"
            elif "dashboard" in lowered or "admin" in lowered:
                lead.project_type = "Dashboard or admin panel"
            elif "app" in lowered or "application" in lowered:
                lead.project_type = "Custom application"
            elif "landing" in lowered:
                lead.project_type = "Landing page"
            elif "website" in lowered or "web site" in lowered:
                lead.project_type = "Business website"
        if lead.agreed is True:
            lead.status = "agreed"
        elif lead.agreed is False:
            lead.status = "not_agreed"
        elif lead.name and lead.need and lead.budget and lead.status not in {
            "agreed",
            "not_agreed",
            "needs_team",
        }:
            lead.status = "qualified"
        elif lead.need and lead.status not in {"agreed", "not_agreed", "needs_team"}:
            lead.status = "collecting"
        return lead

    def _extract_name(self, message: str) -> str | None:
        patterns = [
            r"(?:my name is|name is|i am|this is|నేను)\s+([A-Za-z .]{2,40})",
            r"(?:naa peru|na peru)\s+([A-Za-z .]{2,40})",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip(" .")
        return None

    def _extract_budget(self, message: str) -> str | None:
        match = re.search(
            r"(?:₹|rs\.?|inr)?\s?(\d+(?:,\d+)*(?:\.\d+)?)\s?(k|lakh|lakhs|cr|crore|crores)?",
            message,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        amount = match.group(1)
        suffix = match.group(2) or ""
        return f"{amount} {suffix}".strip()

    def _extract_agreement(self, message: str) -> bool | None:
        lowered = message.lower()
        positive = ("yes", "ok", "okay", "agreed", "agree", "fine", "proceed", "sure", "సరే")
        negative = ("no", "not interested", "later", "లేదు", "వద్దు", "కాదు")
        if any(term in lowered for term in positive):
            return True
        if any(term in lowered for term in negative):
            return False
        return None

    def _is_repeated_intro(self, reply: str) -> bool:
        normalized = reply.strip()
        if not normalized:
            return False
        return "కావిత" in normalized and "డెవలప్" in normalized and "సహాయం" in normalized

    def _development_reply(self, lead: LeadDetails, message: str) -> str:
        lowered = message.lower()
        if lead.status == "agreed":
            return "చాలా ధన్యవాదాలు అండి. మా టీమ్ త్వరలో మీకు తిరిగి కాల్ చేస్తుంది."
        if lead.status == "not_agreed":
            return "పరవాలేదు అండి. అవసరం ఉంటే మా టీమ్ తర్వాత సహాయం చేస్తుంది."
        if "ecommerce" in lowered or "e-commerce" in lowered:
            return (
                "తప్పకుండా అండి. ఈకామర్స్‌కు ప్రొడక్ట్ లిస్టింగ్, పేమెంట్, ఆర్డర్లు, "
                "అడ్మిన్ ప్యానెల్ అవసరం అవుతాయి. మీ బడ్జెట్ రేంజ్ ఎంత?"
            )
        if "payment" in lowered:
            return (
                "పేమెంట్ గేట్‌వే చేయవచ్చు అండి. Razorpay లేదా Stripe సరిపోతాయి. "
                "ఇంకే ఫీచర్లు కావాలి?"
            )
        if "dashboard" in lowered or "admin" in lowered:
            return (
                "అడ్మిన్ ప్యానెల్ చేయవచ్చు అండి. యూజర్ రోల్స్, రిపోర్ట్స్, "
                "డేటా మేనేజ్‌మెంట్ అవసరమా?"
            )
        if "app" in lowered or "application" in lowered:
            return (
                "కస్టమ్ యాప్ చేయవచ్చు అండి. లాగిన్, డేటాబేస్, అడ్మిన్ ప్యానెల్ అవసరమా?"
            )
        if "seo" in lowered:
            return "SEO-ready structure, speed, meta tags, analytics సెట్ చేయవచ్చు అండి. మీది కొత్త సైటా?"
        if "domain" in lowered or "hosting" in lowered:
            return "డొమైన్, హోస్టింగ్ సెటప్‌లో కూడా సహాయం చేస్తాం అండి. మీ దగ్గర ఇప్పటికే డొమైన్ ఉందా?"
        if "budget" in lowered or "cost" in lowered or "price" in lowered:
            return (
                "ధర ఫీచర్లపై ఆధారపడుతుంది అండి. ముందుగా మీ అవసరం, పేజీలు, ఫీచర్లు తెలుసుకుని "
                "టీమ్ ఫైనల్ ఎస్టిమేట్ చెప్తుంది."
            )
        if "timeline" in lowered or "time" in lowered:
            return "టైమ్‌లైన్ స్కోప్‌పై ఆధారపడుతుంది అండి. మీకు ఎప్పటిలో లాంచ్ కావాలి?"
        if "website" in lowered or "web site" in lowered:
            return (
                "వెబ్‌సైట్ చేయవచ్చు అండి. పేజీలు, డిజైన్, ఫారమ్, WhatsApp, SEO అవసరమా?"
            )
        if lead.need:
            return (
                "అర్థమైంది అండి. దీనికి సరైన ఫీచర్లు, డిజైన్, బడ్జెట్ చూసి ప్లాన్ చేస్తాం. "
                "మీ బడ్జెట్ రేంజ్ ఎంత?"
            )
        return "తప్పకుండా అండి. మీకు కావాల్సిన డెవలప్‌మెంట్ అవసరాన్ని కొంచెం వివరంగా చెప్పగలరా?"

    def _event_instruction(self, event: str) -> str:
        if event == "caller_message":
            return (
                "This is not the first turn. Do not introduce yourself again. "
                "Answer the caller's latest development requirement first, "
                "then ask the next useful question."
            )
        if event == "no_speech_detected":
            return "Ask politely to repeat. Do not end the call immediately."
        return "Start the call with the exact Kavitha/Rubicorn greeting."

    def _fallback_reply(self, lead: LeadDetails) -> str:
        if lead.status == "agreed":
            return "చాలా ధన్యవాదాలు అండి. మా రూబికార్న్ టెక్నాలజీస్ టీమ్ త్వరలో మీకు తిరిగి కాల్ చేస్తుంది."
        if lead.status == "needs_team":
            return "క్షమించండి అండి, దీనిని మా టీమ్‌తో నిర్ధారించి మీకు తిరిగి కాల్ చేస్తాము."
        if not lead.name:
            return self.initial_greeting()
        if not lead.need:
            return "మీకు వెబ్‌సైట్, ఈకామర్స్, ల్యాండింగ్ పేజ్ లేదా కస్టమ్ వెబ్ యాప్‌లో ఏది కావాలి?"
        if not lead.budget:
            return "ఈ ప్రాజెక్ట్ కోసం మీ బడ్జెట్ రేంజ్ ఎంతగా అనుకుంటున్నారు?"
        return "మీ వివరాలు నమోదు చేశాను. మా టీమ్ మీకు తిరిగి కాల్ చేయడం సరేనా?"

    def _system_prompt(self) -> str:
        lines = [
            "నువ్వు కావిత. రూబికార్న్ టెక్నాలజీస్ వెబ్ డెవలప్‌మెంట్ కంపెనీకి చెందిన మర్యాదగల మహిళా వాయిస్ కన్సల్టెంట్.",
            "ఎల్లప్పుడూ స్వచ్ఛమైన, సహజమైన, వినయపూర్వకమైన తెలుగులో మాత్రమే సమాధానం ఇవ్వాలి.",
            "ఇంగ్లీష్ లేదా టెంగ్లిష్ వాడకూడదు. కాలర్ ఇంగ్లీష్‌లో మాట్లాడినా తెలుగులోనే కొనసాగాలి.",
            "వాయిస్ కాల్ కాబట్టి ప్రతి సమాధానం సహజంగా, చిన్నగా, స్పష్టంగా, మృదువుగా ఉండాలి.",
            "ముందుగా కాలర్ చెప్పింది అర్థం చేసుకుని దానికి ఉపయోగకరంగా సమాధానం చెప్పాలి. "
            "వెంటనే పేరు మాత్రమే అడుగుతూ నిలిచిపోకూడదు.",
            "caller_message event లో పరిచయం మళ్లీ చెప్పకూడదు. కాలర్ చెప్పిన అవసరానికి ముందుగా సమాధానం ఇవ్వాలి.",
            "ఒక్కసారికి అవసరమైనప్పుడు ఒక్క ప్రశ్న మాత్రమే అడగాలి, కానీ కాలర్ ప్రశ్న అడిగితే "
            "ముందుగా దానికి సమాధానం ఇవ్వాలి.",
            "event call_started అయితే ఖచ్చితంగా ఇలా ప్రారంభించాలి: "
            "హలో అండి, నేను రూబికార్న్ టెక్నాలజీస్ నుండి కావిత మాట్లాడుతున్నాను. "
            "మీకు ఏ డెవలప్‌మెంట్ సహాయం కావాలి?",
            "event no_speech_detected అయితే వినిపించలేదని మర్యాదగా చెప్పి మళ్లీ చెప్పమని అడగాలి.",
            "కాలర్ అవసరం తెలిసిన తర్వాత మాత్రమే వివరాలు సేకరించాలి: పేరు, ఫోన్, "
            "ప్రాజెక్ట్ రకం, అవసరం, బడ్జెట్, టైమ్‌లైన్, కాల్‌బ్యాక్ అంగీకారం.",
            "వెబ్‌సైట్, ఈకామర్స్, ల్యాండింగ్ పేజ్, డ్యాష్‌బోర్డ్, CRM, హోస్టింగ్, "
            "డొమైన్, SEO, పేమెంట్ ఇంటిగ్రేషన్, మొబైల్ యాప్, API, డేటాబేస్, "
            "అడ్మిన్ ప్యానెల్, బుకింగ్ సిస్టమ్, ఆటోమేషన్, AI చాట్‌బాట్, "
            "మెయింటెనెన్స్, రీడిజైన్, స్పీడ్ ఆప్టిమైజేషన్ విషయాల గురించి మాట్లాడగలగాలి.",
            "అవసరాన్ని బట్టి సరళమైన సలహా ఇవ్వాలి: ఏ టెక్నాలజీ సరిపోతుంది, "
            "ఏ ఫీచర్లు అవసరం, ప్రాసెస్ ఎలా ఉంటుంది, బడ్జెట్ ఎలా అంచనా వేయాలి, "
            "టైమ్‌లైన్ ఎలా ప్లాన్ చేయాలి.",
            "ఫిక్స్‌డ్ ధర లేదా ఖచ్చితమైన డెలివరీ తేదీ హామీ ఇవ్వకూడదు. "
            "వివరాలు తీసుకుని టీమ్ ఫైనల్ ఎస్టిమేట్ చెప్తుందని చెప్పాలి.",
            "తెలియని లేదా వెబ్/సాఫ్ట్‌వేర్ డెవలప్‌మెంట్‌కు సంబంధం లేని ప్రశ్న అయితే "
            "టీమ్‌తో చెక్ చేసి తిరిగి కాల్ చేస్తామని చెప్పి status needs_team చేయాలి.",
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
