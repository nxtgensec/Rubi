import re
from pathlib import Path


class WebsiteKnowledgeService:
    def __init__(self) -> None:
        self.knowledge_path = Path(__file__).resolve().parents[3] / "docs" / "business_knowledge.md"

    def answer(self, question: str) -> str:
        knowledge = self.load_knowledge()
        if not knowledge:
            return (
                "Website knowledge is not configured yet. I can still collect your requirement, "
                "budget, name, and contact details for the team."
            )

        query_terms = {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9]+", question)
            if len(term) >= 4
        }
        paragraphs = [
            paragraph.strip()
            for paragraph in knowledge.split("\n\n")
            if paragraph.strip()
        ]
        ranked = sorted(
            paragraphs,
            key=lambda paragraph: len(query_terms.intersection(paragraph.lower().split())),
            reverse=True,
        )
        best = ranked[0] if ranked else knowledge[:320]
        return best[:420]

    def load_knowledge(self) -> str:
        if not self.knowledge_path.exists():
            return ""
        return self.knowledge_path.read_text(encoding="utf-8").strip()


website_knowledge_service = WebsiteKnowledgeService()
