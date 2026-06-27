from pydantic import BaseModel, Field


class VisitCreate(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=128)
    user_agent: str | None = None


class VisitStats(BaseModel):
    visit_date: str
    today_visits: int
    total_visits: int
