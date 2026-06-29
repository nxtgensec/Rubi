import re

import httpx
from app.schemas.intake import LeadDetails
from app.services.gemini_agent_service import gemini_agent_service
from app.services.storage_service import storage_service
from app.services.website_knowledge_service import website_knowledge_service


class IntakeAgentService:
    async def process_caller_message(
        self,
        call_id: str,
        message: str,
        from_number: str,
    ) -> str:
        call = storage_service.get_call(call_id)
        if not call:
            raise KeyError(call_id)

        language = self.detect_conversation_language(message)
        storage_service.append_transcript(call_id, "user", message, language)
        call = storage_service.get_call(call_id)
        if not call:
            raise KeyError(call_id)

        try:
            lead, response, response_language, _should_end = await gemini_agent_service.process(
                call,
                message,
            )
            lead.phone = lead.phone or from_number
            lead.language = response_language
            storage_service.update_lead(call_id, lead)
            stored_call = storage_service.get_call(call_id)
            if stored_call:
                stored_call.language = response_language
                storage_service.upsert_call(stored_call)
            storage_service.append_transcript(call_id, "assistant", response, response_language)
            return response
        except (RuntimeError, httpx.HTTPError, ValueError, KeyError):
            pass

        lead = self.extract_lead_details(call.lead, message, from_number, language)
        storage_service.update_lead(call_id, lead)

        response = self.next_response(lead, message, language)
        storage_service.append_transcript(call_id, "assistant", response, language)
        return response

    def extract_lead_details(
        self,
        current: LeadDetails,
        message: str,
        from_number: str,
        language: str,
    ) -> LeadDetails:
        lead = current.model_copy(deep=True)
        lead.phone = lead.phone or from_number
        lead.language = language

        name = self._extract_name(message)
        if name:
            lead.name = name

        budget = self._extract_budget(message)
        if budget:
            lead.budget = budget

        if not lead.need:
            lead.need = self._extract_need(message)

        if self._is_out_of_scope(message):
            lead.status = "needs_team"
            return lead

        agreement = self._extract_agreement(message)
        if agreement is not None:
            lead.agreed = agreement

        if lead.agreed is True:
            lead.status = "agreed"
        elif lead.agreed is False:
            lead.status = "not_agreed"
        elif lead.name and lead.need and lead.budget:
            lead.status = "qualified"
        else:
            lead.status = "collecting"
        return lead

    def next_response(self, lead: LeadDetails, message: str, language: str) -> str:
        if lead.status == "needs_team":
            return self._phrase(
                language,
                "Sorry, ee question gurinchi exact answer na daggara ledu. "
                "Nenu maa team ki connect chesthanu. Vallu meeku callback chestharu.",
            )
        if lead.agreed is True:
            return self._phrase(
                language,
                "Chala bagundi, thank you. Nenu maa Rubi team ki connect chesthanu. "
                "Maa team tondaraga meeku call back chestharu.",
            )
        if lead.agreed is False:
            return self._phrase(
                language,
                "Parvaledu. Meeru ippudu ready ga leru ani note chesanu. "
                "Tarvata kavali ante maa team help chestharu.",
            )
        if not lead.name:
            return self._phrase(language, "Mee peru cheppagalara?")
        if not lead.need:
            website_answer = website_knowledge_service.answer(message)
            return self._phrase(
                language,
                f"{website_answer} Meeku website, ecommerce, landing page, "
                "leka custom web app lo exactly emi kavali?",
            )
        if not lead.budget:
            website_answer = website_knowledge_service.answer(lead.need or message)
            return self._phrase(
                language,
                f"{website_answer} Ee project kosam mee budget range entha plan chestunnaru?",
            )
        return self._phrase(
            language,
            "Mee details note chesanu. Maa Rubi team meeku callback cheyyadam okay na?",
        )

    def detect_conversation_language(self, message: str) -> str:
        if any("\u0c00" <= char <= "\u0c7f" for char in message):
            return "te-IN"
        telugu_words = ["naku", "kavali", "emi", "meeru", "budget", "cheppandi", "undi", "ledu"]
        if any(word in message.lower() for word in telugu_words):
            return "tenglish"
        return "en-IN"

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

    def _extract_need(self, message: str) -> str | None:
        cleaned = message.strip()
        if len(cleaned) < 8:
            return None
        if self._extract_agreement(cleaned) is not None and len(cleaned.split()) <= 4:
            return None
        if self._is_out_of_scope(cleaned):
            return None
        return cleaned[:240]

    def _extract_agreement(self, message: str) -> bool | None:
        lowered = message.lower()
        positive = ["yes", "ok", "okay", "agreed", "agree", "fine", "interested", "proceed", "sure"]
        positive += ["avunu", "sare", "okay", "oppukuntunna", "yes cheyyandi"]
        negative = ["no", "not interested", "don't", "dont", "later", "ledu", "vaddu", "kaadu"]
        if any(term in lowered for term in positive):
            return True
        if any(term in lowered for term in negative):
            return False
        return None

    def _phrase(self, language: str, english: str) -> str:
        if language in {"te-IN", "tenglish"}:
            return english
        return english

    def _is_out_of_scope(self, message: str) -> bool:
        lowered = message.lower()
        question_markers = ["what", "how", "why", "when", "where", "who", "emi", "ela", "enduku"]
        web_terms = [
            "website",
            "web",
            "app",
            "application",
            "ecommerce",
            "landing",
            "dashboard",
            "booking",
            "domain",
            "hosting",
            "seo",
            "payment",
            "crm",
            "design",
            "development",
            "budget",
            "page",
            "pages",
            "store",
            "wordpress",
            "shopify",
        ]
        unrelated_terms = [
            "weather",
            "politics",
            "movie",
            "cricket",
            "news",
            "joke",
            "song",
            "medical",
            "doctor",
            "loan",
            "stock",
        ]
        has_question = "?" in lowered or any(marker in lowered for marker in question_markers)
        has_web_context = any(term in lowered for term in web_terms)
        has_unrelated_context = any(term in lowered for term in unrelated_terms)
        return (
            has_question
            and not has_web_context
            and len(lowered.split()) > 4
        ) or has_unrelated_context


intake_agent_service = IntakeAgentService()
