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
            "హలో అండి, నేను కావిత, రూబికార్న్ టెక్నాలజీస్ నుంచి మాట్లాడుతున్నాను. "
            "మీకు వెబ్‌సైట్ లేదా యాప్‌లో ఏ సహాయం కావాలి?"
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

        if event == "caller_message":
            lead = self._hydrate_development_need(call.lead.model_copy(deep=True), message)
            lead.language = "te-IN"
            lead.preferred_language = lead.preferred_language or "Telugu"
            reply = await self._call_text_reply(call, message)
            if not reply or self._needs_dynamic_retry(reply, call):
                reply = self._dynamic_fallback_reply(message)
            should_end = lead.status in {"agreed", "not_agreed", "needs_team"}
            return lead, reply, "te-IN", should_end

        raw = await self._call_chat_completion(call, message, event)
        result = self._parse_result(raw)
        lead = self._merge_lead(call.lead, result)
        if event == "caller_message":
            lead = self._hydrate_development_need(lead, message)
        language = "te-IN"
        lead.language = language
        lead.preferred_language = lead.preferred_language or "Telugu"

        reply = str(result.get("reply") or "").strip()
        if event == "caller_message" and self._needs_dynamic_retry(reply, call):
            retry_reply = await self._call_text_reply(
                call,
                message,
            )
            if retry_reply and not self._is_repeated_intro(retry_reply):
                reply = retry_reply
            else:
                reply = self._dynamic_fallback_reply(message)
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
            "temperature": 0.45,
            "max_tokens": 160,
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
            return self._message_text(message_data, choices[0])
        return str(data.get("output_text") or data.get("text") or data)

    async def _call_text_reply(self, call: StoredCall, message: str) -> str:
        body = {
            "model": settings.sarvam_chat_model,
            "temperature": 0.55,
            "max_tokens": 1600,
            "messages": [
                {
                    "role": "system",
                    "content": self._text_reply_prompt(),
                },
                {
                    "role": "user",
                    "content": self._text_reply_payload(call, message),
                },
            ],
        }
        async with httpx.AsyncClient(timeout=25) as client:
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
            return self._message_text(message_data, choices[0]).strip()
        return str(data.get("output_text") or data.get("text") or "").strip()

    def _message_text(self, message_data: dict[str, Any], choice: dict[str, Any]) -> str:
        content = message_data.get("content") or choice.get("text")
        if content:
            text = str(content)
            if self._has_too_much_english(text):
                reasoning_text = self._extract_telugu_from_reasoning(
                    str(message_data.get("reasoning_content") or "")
                )
                return reasoning_text or ""
            return text
        reasoning = str(message_data.get("reasoning_content") or "")
        return self._extract_telugu_from_reasoning(reasoning)

    def _has_too_much_english(self, text: str) -> bool:
        return len(re.findall(r"[A-Za-z]", text)) > 12

    def _extract_telugu_from_reasoning(self, reasoning: str) -> str:
        quoted = re.findall(r'"([^"]*[\u0c00-\u0c7f][^"]*)"', reasoning)
        clean_quoted = [
            item.strip()
            for item in quoted
            if len(re.findall(r"[A-Za-z]", item)) < 4
        ]
        if clean_quoted:
            return clean_quoted[-1]
        sentences = re.findall(r"[^.\n?!]*[\u0c00-\u0c7f][^.\n?!]*[.?!]?", reasoning)
        clean_sentences = [
            item.strip()
            for item in sentences
            if len(re.findall(r"[A-Za-z]", item)) < 4
        ]
        return clean_sentences[-1] if clean_sentences else ""

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

    def _text_reply_payload(self, call: StoredCall, message: str) -> str:
        transcript = [
            {"role": turn.role, "text": turn.text}
            for turn in call.transcript[-8:]
        ]
        payload = {
            "latest_caller_message": message,
            "recent_transcript": transcript,
            "current_lead": call.lead.model_dump(),
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
            elif self._mentions_app(lowered):
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

    def _mentions_app(self, lowered: str) -> bool:
        return bool(re.search(r"\bapp\b|\bapplication\b", lowered))

    def _is_repeated_intro(self, reply: str) -> bool:
        normalized = reply.strip()
        if not normalized:
            return False
        return "కావిత" in normalized and "డెవలప్" in normalized and "సహాయం" in normalized

    def _needs_dynamic_retry(self, reply: str, call: StoredCall) -> bool:
        normalized = " ".join(reply.split())
        if not normalized or self._is_repeated_intro(normalized):
            return True
        if "దానికి తగ్గట్టు ప్లాన్ చేయవచ్చు" in normalized:
            return True
        previous_assistant = next(
            (
                " ".join(turn.text.split())
                for turn in reversed(call.transcript)
                if turn.role == "assistant"
            ),
            "",
        )
        return bool(previous_assistant and normalized == previous_assistant)

    def _development_reply(self, lead: LeadDetails, message: str) -> str:
        lowered = message.lower()
        if lead.status == "agreed":
            return "ధన్యవాదాలు అండి. మా టీమ్ త్వరలో మీకు కాల్ చేస్తుంది."
        if lead.status == "not_agreed":
            return "పరవాలేదు అండి. అవసరం అయితే తర్వాత సహాయం చేస్తాం."
        if "ecommerce" in lowered or "e-commerce" in lowered:
            return (
                "సరే అండి. ఈకామర్స్‌కు ప్రొడక్ట్స్, పేమెంట్, ఆర్డర్లు ఉంటాయి. "
                "మీ బడ్జెట్ ఎంత?"
            )
        if "payment" in lowered:
            return (
                "అవును అండి, పేమెంట్ గేట్‌వే చేయవచ్చు. "
                "ఇంకే ఫీచర్లు కావాలి?"
            )
        if "dashboard" in lowered or "admin" in lowered:
            return (
                "అడ్మిన్ ప్యానెల్ చేయవచ్చు అండి. "
                "రిపోర్ట్స్, యూజర్ రోల్స్ కావాలా?"
            )
        if self._mentions_app(lowered):
            return (
                "కస్టమ్ యాప్ చేయవచ్చు అండి. లాగిన్, డేటాబేస్, అడ్మిన్ ప్యానెల్ కావాలా?"
            )
        if "seo" in lowered:
            return "SEO, స్పీడ్, అనలిటిక్స్ సెట్ చేయవచ్చు అండి. మీది కొత్త సైటా?"
        if "domain" in lowered or "hosting" in lowered:
            return "డొమైన్, హోస్టింగ్ కూడా సెట్ చేస్తాం అండి. డొమైన్ ఇప్పటికే ఉందా?"
        if "budget" in lowered or "cost" in lowered or "price" in lowered:
            return (
                "ధర ఫీచర్లపై ఆధారపడుతుంది అండి. "
                "మీ అవసరం తెలుసుకుని టీమ్ ఎస్టిమేట్ చెప్తుంది."
            )
        if "timeline" in lowered or "time" in lowered:
            return "టైమ్‌లైన్ స్కోప్‌పై ఆధారపడుతుంది అండి. ఎప్పటిలో లాంచ్ కావాలి?"
        if "website" in lowered or "web site" in lowered:
            return (
                "వెబ్‌సైట్ చేయవచ్చు అండి. పేజీలు, ఫారమ్, వాట్సాప్, SEO కావాలా?"
            )
        if lead.need:
            return (
                "అర్థమైంది అండి. దీనికి సరైన ప్లాన్ చేయవచ్చు. "
                "మీ బడ్జెట్ ఎంత?"
            )
        return "సరే అండి. మీకు ఏ పని కావాలో కొంచెం వివరంగా చెప్పగలరా?"

    def _dynamic_fallback_reply(self, message: str) -> str:
        if len(message.strip()) > 12:
            return (
                "అర్థమైంది అండి. దానికి తగ్గట్టు ప్లాన్ చేయవచ్చు. "
                "మీకు ముఖ్యంగా ఏ ఫీచర్ కావాలి?"
            )
        return "సరే అండి. ఇంకొంచెం వివరంగా చెప్తారా?"

    def _text_reply_prompt(self) -> str:
        return "\n".join(
            [
                "నువ్వు కావిత, రూబికార్న్ టెక్నాలజీస్ నుంచి మాట్లాడుతున్నావు.",
                "కేవలం సహజమైన తెలుగులో మాత్రమే మాట్లాడాలి.",
                "English letters అసలు వాడకూడదు. English పదాలను కూడా తెలుగు లిపిలో చెప్పాలి.",
                "JSON ఇవ్వకూడదు. లేబుల్స్ ఇవ్వకూడదు. ఒక్క phone-call reply మాత్రమే ఇవ్వాలి.",
                "కాలర్ చివరిగా అడిగిన ప్రశ్నకు నేరుగా సమాధానం ఇవ్వాలి.",
                "ముందు చెప్పిన మాటలు మళ్లీ repeat చేయకూడదు.",
                "అదే ప్రశ్నను మళ్లీ అడగకూడదు.",
                "వెబ్‌సైట్, యాప్, ఈకామర్స్, పేమెంట్, డ్యాష్‌బోర్డ్, CRM, హోస్టింగ్, SEO లాంటి development విషయాలకు సహాయం చేయాలి.",
                "సమాధానం రెండు చిన్న వాక్యాల్లో ఉండాలి.",
                "చివర్లో అవసరమైతే ఒక్క చిన్న follow-up question అడగాలి.",
            ]
        )

    def _event_instruction(self, event: str) -> str:
        if event == "caller_message":
            return (
                "This is not the first turn. Do not introduce yourself again. "
                "Answer the caller's latest development requirement first, "
                "then ask the next useful question. Do not reuse a fixed template."
            )
        if event == "caller_message_retry":
            return (
                "Your previous answer was invalid or repetitive. Give a fresh, dynamic, "
                "short Telugu answer to the caller's exact latest message. "
                "Do not introduce yourself. Do not repeat earlier questions."
            )
        if event == "no_speech_detected":
            return "Ask politely to repeat. Do not end the call immediately."
        return "Start the call with the exact Kavitha/Rubicorn greeting."

    def _fallback_reply(self, lead: LeadDetails) -> str:
        if lead.status == "agreed":
            return "ధన్యవాదాలు అండి. మా టీమ్ త్వరలో మీకు కాల్ చేస్తుంది."
        if lead.status == "needs_team":
            return "క్షమించండి అండి. ఇది మా టీమ్‌తో చూసి మీకు కాల్ చేస్తాము."
        if not lead.name:
            return self.initial_greeting()
        if not lead.need:
            return "మీకు వెబ్‌సైట్, ఈకామర్స్, ల్యాండింగ్ పేజ్ లేదా కస్టమ్ వెబ్ యాప్‌లో ఏది కావాలి?"
        if not lead.budget:
            return "ఈ పని కోసం మీ బడ్జెట్ ఎంత అండి?"
        return "మీ వివరాలు నోట్ చేశాను అండి. మా టీమ్ కాల్ చేయడం సరేనా?"

    def _system_prompt(self) -> str:
        lines = [
            "నువ్వు కావిత. రూబికార్న్ టెక్నాలజీస్ వెబ్ డెవలప్‌మెంట్ కంపెనీకి చెందిన మర్యాదగల మహిళా వాయిస్ కన్సల్టెంట్.",
            "ఎల్లప్పుడూ స్వచ్ఛమైన, సహజమైన, వినయపూర్వకమైన తెలుగులో మాత్రమే సమాధానం ఇవ్వాలి.",
            "ఇంగ్లీష్ లేదా టెంగ్లిష్ వాడకూడదు. కాలర్ ఇంగ్లీష్‌లో మాట్లాడినా తెలుగులోనే కొనసాగాలి.",
            "వాయిస్ కాల్ కాబట్టి ప్రతి సమాధానం సహజంగా, చిన్నగా, స్పష్టంగా, మృదువుగా ఉండాలి.",
            "స్క్రిప్ట్‌లా కాకుండా మనిషిలా మాట్లాడాలి. పెద్ద లిస్టులు చెప్పకూడదు.",
            "సాధారణంగా ఒకటి లేదా రెండు చిన్న వాక్యాలు మాత్రమే చెప్పాలి.",
            "ప్రతి caller_message కి కాలర్ చివరిగా చెప్పిన మాటల ఆధారంగా కొత్త సమాధానం ఇవ్వాలి.",
            "అదే ప్రశ్నను మళ్లీ మళ్లీ అడగకూడదు. అవసరం అయితే మాత్రమే తదుపరి ప్రశ్న అడగాలి.",
            "కాల్‌లో ముందు మాట్లాడిన విషయాన్ని గుర్తుపెట్టుకుని కొనసాగాలి.",
            "ముందుగా కాలర్ చెప్పింది అర్థం చేసుకుని దానికి ఉపయోగకరంగా సమాధానం చెప్పాలి. "
            "వెంటనే పేరు మాత్రమే అడుగుతూ నిలిచిపోకూడదు.",
            "caller_message event లో పరిచయం మళ్లీ చెప్పకూడదు. కాలర్ చెప్పిన అవసరానికి ముందుగా సమాధానం ఇవ్వాలి.",
            "ఒక్కసారికి అవసరమైనప్పుడు ఒక్క ప్రశ్న మాత్రమే అడగాలి, కానీ కాలర్ ప్రశ్న అడిగితే "
            "ముందుగా దానికి సమాధానం ఇవ్వాలి.",
            "event call_started అయితే ఖచ్చితంగా ఇలా ప్రారంభించాలి: "
            "హలో అండి, నేను కావిత, రూబికార్న్ టెక్నాలజీస్ నుంచి మాట్లాడుతున్నాను. "
            "మీకు వెబ్‌సైట్ లేదా యాప్‌లో ఏ సహాయం కావాలి?",
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
