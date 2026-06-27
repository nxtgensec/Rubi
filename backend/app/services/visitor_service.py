from datetime import UTC, datetime
from typing import Any

import httpx
from app.core.config import settings
from app.schemas.visit import VisitStats


class SupabaseNotConfiguredError(RuntimeError):
    pass


class VisitorService:
    def __init__(self) -> None:
        self.base_url = (settings.supabase_url or "").rstrip("/")
        self.service_key = settings.supabase_service_role_key

    async def get_stats(self) -> VisitStats:
        today = self._today()
        await self._ensure_today_row(today)
        await self._reconcile_today(today)
        rows = await self._request(
            "GET",
            "/rest/v1/visitor_daily_counts?select=visit_date,visit_count",
        )
        total = sum(int(row.get("visit_count", 0)) for row in rows)
        today_row = next((row for row in rows if row.get("visit_date") == today), None)
        return VisitStats(
            visit_date=today,
            today_visits=int(today_row.get("visit_count", 0)) if today_row else 0,
            total_visits=total,
        )

    async def record_visit(self, visitor_id: str, user_agent: str | None) -> VisitStats:
        today = self._today()
        await self._ensure_today_row(today)
        existing = await self._request(
            "GET",
            "/rest/v1/visitor_events"
            f"?select=id&visit_date=eq.{today}&visitor_id=eq.{visitor_id}&limit=1",
        )
        if not existing:
            await self._request(
                "POST",
                "/rest/v1/visitor_events",
                json={
                    "visit_date": today,
                    "visitor_id": visitor_id,
                    "user_agent": user_agent,
                },
                headers={"Prefer": "return=minimal"},
            )
            await self._increment_today(today)
        else:
            await self._reconcile_today(today)
        return await self.get_stats()

    async def _ensure_today_row(self, today: str) -> None:
        await self._request(
            "POST",
            "/rest/v1/visitor_daily_counts?on_conflict=visit_date",
            json={
                "visit_date": today,
                "visit_count": 0,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            headers={"Prefer": "resolution=ignore-duplicates,return=minimal"},
        )

    async def _increment_today(self, today: str) -> None:
        rows = await self._request(
            "GET",
            f"/rest/v1/visitor_daily_counts?select=visit_count&visit_date=eq.{today}&limit=1",
        )
        current = int(rows[0].get("visit_count", 0)) if rows else 0
        await self._request(
            "PATCH",
            f"/rest/v1/visitor_daily_counts?visit_date=eq.{today}",
            json={
                "visit_count": current + 1,
                "updated_at": datetime.now(UTC).isoformat(),
            },
            headers={"Prefer": "return=minimal"},
        )

    async def _reconcile_today(self, today: str) -> None:
        rows = await self._request(
            "GET",
            f"/rest/v1/visitor_events?select=id&visit_date=eq.{today}",
        )
        event_count = len(rows)
        daily_rows = await self._request(
            "GET",
            f"/rest/v1/visitor_daily_counts?select=visit_count&visit_date=eq.{today}&limit=1",
        )
        current = int(daily_rows[0].get("visit_count", 0)) if daily_rows else 0
        if event_count != current:
            await self._request(
                "PATCH",
                f"/rest/v1/visitor_daily_counts?visit_date=eq.{today}",
                json={
                    "visit_count": event_count,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
                headers={"Prefer": "return=minimal"},
            )

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        if not self.base_url or not self.service_key:
            raise SupabaseNotConfiguredError("Supabase is not configured")
        request_headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            **(headers or {}),
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(
                method,
                f"{self.base_url}{path}",
                json=json,
                headers=request_headers,
            )
        response.raise_for_status()
        if not response.content:
            return []
        return response.json()

    def _today(self) -> str:
        return datetime.now(UTC).date().isoformat()


visitor_service = VisitorService()
