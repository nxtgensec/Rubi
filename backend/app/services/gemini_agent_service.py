import json
import sys
from typing import Any

import httpx
from app.core.config import settings
from app.schemas.intake import LeadDetails, StoredCall
from app.services.website_knowledge_service import website_knowledge_service


class GeminiAgentService:
    async def process(self, call: StoredCall, message: str) -> tuple[LeadDetails, str, str, bool]:
        if "pytest" in sys.modules:
            raise RuntimeError("Gemini is disabled during tests")
        if not settings.gemini_api_key:
            raise RuntimeError("Gemini API key is not configured")

        payload = self._request_payload(call, message)
        try:
            raw = await self._call_interactions(payload)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in {400, 404}:
                raise
            raw = await self._call_generate_content(payload)
        result = self._parse_result(raw)
        lead = self._merge_lead(call.lead, result)
        language = self._normalise_language(result.get("language") or lead.language)
        reply = str(result.get("reply") or "").strip()
        if not reply:
            reply = self._fallback_reply(lead, language)
        should_end = bool(result.get("should_end_call")) or lead.status in {
            "agreed",
            "not_agreed",
            "needs_team",
        }
        return lead, reply, language, should_end

    def _request_payload(self, call: StoredCall, message: str) -> dict[str, Any]:
        transcript = [
            {
                "role": turn.role,
                "text": turn.text,
                "language": turn.language,
            }
            for turn in call.transcript[-12:]
        ]
        website_context = website_knowledge_service.answer(message)
        return {
            "model": settings.gemini_model,
            "system_instruction": self._system_prompt(),
            "input": json.dumps(
                {
                    "business": "Rubi web development team",
                    "caller_number": call.from_number,
                    "current_lead": call.lead.model_dump(),
                    "latest_caller_message": message,
                    "recent_transcript": transcript,
                    "website_context": website_context,
                },
                ensure_ascii=False,
            ),
            "generation_config": {
                "temperature": 0.35,
                "response_mime_type": "application/json",
            },
        }

    async def _call_interactions(self, payload: dict[str, Any]) -> str:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/interactions",
                headers={
                    "x-goog-api-key": settings.gemini_api_key or "",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        return str(data.get("output_text") or data.get("text") or data)

    async def _call_generate_content(self, payload: dict[str, Any]) -> str:
        model = settings.gemini_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {
            "systemInstruction": {
                "parts": [{"text": payload["system_instruction"]}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": payload["input"]}],
                }
            ],
            "generationConfig": payload["generation_config"],
        }
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                url,
                params={"key": settings.gemini_api_key},
                headers={"Content-Type": "application/json"},
                json=body,
            )
            response.raise_for_status()
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(str(part.get("text", "")) for part in parts)

    def _parse_result(self, raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.removeprefix("json").strip()
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
            "language",
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
            if lowered in {"true", "yes", "agreed", "agree"}:
                lead.agreed = True
            elif lowered in {"false", "no", "not_agreed", "not agreed"}:
                lead.agreed = False

        if not lead.status or lead.status == "collecting":
            if lead.agreed is True:
                lead.status = "agreed"
            elif lead.agreed is False:
                lead.status = "not_agreed"
            elif lead.name and lead.need and lead.budget:
                lead.status = "qualified"
            else:
                lead.status = "collecting"
        return lead

    def _normalise_language(self, language: str) -> str:
        lowered = language.lower()
        if "telugu" in lowered or "te-" in lowered:
            return "te-IN"
        if "tenglish" in lowered:
            return "tenglish"
        if "english" in lowered or "en-" in lowered:
            return "en-IN"
        return language if language in {"te-IN", "tenglish", "en-IN"} else "te-IN"

    def _fallback_reply(self, lead: LeadDetails, language: str) -> str:
        if lead.status == "agreed":
            return (
                "Chala thanks. Nenu Rubi team ki connect chesthanu. "
                "Maa team tondaraga call back chestharu."
            )
        if lead.status == "needs_team":
            return (
                "Sorry, idi exact ga confirm cheyyali. Nenu maa team ki connect "
                "chesthanu. Vallu meeku call back chestharu."
            )
        if not lead.preferred_language:
            return (
                "Namaskaram, nenu Rubi nundi maatladutunna. Meeru Telugu, "
                "English, leda Tenglish lo comfortable ga unnara?"
            )
        if not lead.name:
            return "Sure. Mee peru cheppagalara?"
        if not lead.need:
            return (
                "Meeku website, ecommerce store, landing page, dashboard, "
                "leda custom web app lo emi kavali?"
            )
        if not lead.budget:
            return "Ee project kosam approximate budget range entha plan chestunnaru?"
        return "Mee details note chesanu. Rubi team meeku callback cheyyadam okay na?"

    def _system_prompt(self) -> str:
        lines = [
            "You are Rubi, a polite, humble female voice employee for web development.",
            "Primary behavior:",
            "- First ask the caller's comfortable language: Telugu, English, or Tenglish.",
            "- After they answer, continue in that language for the full call.",
            "- Telugu must be natural and accurate.",
            "- For phone TTS, prefer simple spoken Telugu in Latin transliteration.",
            "- Use Telugu script only when the caller uses Telugu script.",
            "- Be warm and human, but keep every response short for a phone call.",
            "- Ask one question at a time.",
            "- Gather: name, phone, preferred language, project type, need, budget range,",
            "  timeline, callback notes, and callback agreement.",
            "- Handle: websites, landing pages, ecommerce, booking systems, dashboards,",
            "  CRM/admin panels, portfolios, redesigns, SEO basics, hosting/domain,",
            "  payment integrations, maintenance, and custom web apps.",
            "- For unknown or non-web questions, politely say you will connect the team,",
            '  set status "needs_team", and end the call.',
            "- If caller agrees to proceed or callback, thank them, say Rubi team will",
            '  get back soon, set agreed true, status "agreed", and end the call.',
            '- If they decline, set agreed false, status "not_agreed", and end the call.',
            "",
            "Return only valid JSON with these keys:",
            "reply, language, preferred_language, name, phone, project_type, need,",
            "budget, timeline, callback_notes, agreed, status, should_end_call, summary.",
            "Use null for unknown fields.",
            "status must be: collecting, qualified, agreed, not_agreed, or needs_team.",
        ]
        return "\n".join(lines)


gemini_agent_service = GeminiAgentService()
