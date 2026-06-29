import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from urllib.parse import quote

import httpx
from app.core.config import settings
from app.schemas.intake import LeadDetails, StoredCall, StoredTranscriptTurn


class StorageService:
    def __init__(self) -> None:
        self.data_dir = self._data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "rubi_store.json"
        self.supabase_url = (settings.supabase_url or "").rstrip("/")
        self.supabase_key = settings.supabase_service_role_key
        self.supabase_enabled = bool(
            self.supabase_url
            and self.supabase_key
            and "pytest" not in sys.modules
        )
        self._migrate_local_calls_to_supabase()

    def list_calls(self) -> list[StoredCall]:
        if self.supabase_enabled:
            try:
                rows = self._supabase_request(
                    "GET",
                    "/rest/v1/rubi_calls?select=call_data&order=created_at.desc",
                )
                return [StoredCall.model_validate(row["call_data"]) for row in rows]
            except (httpx.HTTPError, KeyError, ValueError):
                pass
        data = self._read()
        calls = [StoredCall.model_validate(call) for call in data.get("calls", {}).values()]
        return sorted(calls, key=lambda call: call.created_at, reverse=True)

    def get_call(self, call_id: str) -> StoredCall | None:
        if self.supabase_enabled:
            try:
                rows = self._supabase_request(
                    "GET",
                    f"/rest/v1/rubi_calls?select=call_data&id=eq.{quote(call_id)}&limit=1",
                )
                if rows:
                    return StoredCall.model_validate(rows[0]["call_data"])
            except (httpx.HTTPError, KeyError, ValueError):
                pass
        data = self._read()
        raw = data.get("calls", {}).get(call_id)
        return StoredCall.model_validate(raw) if raw else None

    def get_call_by_provider_id(self, provider_call_id: str) -> StoredCall | None:
        if self.supabase_enabled:
            try:
                rows = self._supabase_request(
                    "GET",
                    "/rest/v1/rubi_calls"
                    f"?select=call_data&provider_call_id=eq.{quote(provider_call_id)}&limit=1",
                )
                if rows:
                    return StoredCall.model_validate(rows[0]["call_data"])
            except (httpx.HTTPError, KeyError, ValueError):
                pass
        for call in self.list_calls():
            if call.provider_call_id == provider_call_id:
                return call
        return None

    def upsert_call(self, call: StoredCall) -> StoredCall:
        call.updated_at = datetime.now(UTC)
        if self.supabase_enabled:
            try:
                self._upsert_supabase_call(call)
            except httpx.HTTPError:
                self._upsert_file_call(call)
        else:
            self._upsert_file_call(call)
        return call

    def append_transcript(
        self,
        call_id: str,
        role: str,
        text: str,
        language: str,
    ) -> StoredCall:
        call = self.get_call(call_id)
        if not call:
            raise KeyError(call_id)
        call.transcript.append(
            StoredTranscriptTurn(
                role=role,
                text=text,
                language=language,
                created_at=datetime.now(UTC),
            )
        )
        call.summary = self.summarize_call(call)
        return self.upsert_call(call)

    def update_lead(self, call_id: str, lead: LeadDetails) -> StoredCall:
        call = self.get_call(call_id)
        if not call:
            raise KeyError(call_id)
        call.lead = lead
        call.summary = self.summarize_call(call)
        return self.upsert_call(call)

    def update_recording(
        self,
        call_id: str,
        recording_status: str,
        recording_url: str | None,
        recording_sid: str | None,
    ) -> StoredCall:
        call = self.get_call(call_id)
        if not call:
            raise KeyError(call_id)
        call.recording_status = recording_status
        call.recording_url = recording_url
        call.recording_sid = recording_sid
        return self.upsert_call(call)

    def summarize_call(self, call: StoredCall) -> str:
        lead = call.lead
        parts = []
        if lead.name:
            parts.append(f"Caller name: {lead.name}")
        if lead.need:
            parts.append(f"Need: {lead.need}")
        if lead.project_type:
            parts.append(f"Project type: {lead.project_type}")
        if lead.budget:
            parts.append(f"Budget: {lead.budget}")
        if lead.timeline:
            parts.append(f"Timeline: {lead.timeline}")
        if lead.preferred_language:
            parts.append(f"Preferred language: {lead.preferred_language}")
        if lead.callback_notes:
            parts.append(f"Callback notes: {lead.callback_notes}")
        if lead.agreed is True:
            parts.append("Agreement: agreed to be contacted by the team")
        elif lead.agreed is False:
            parts.append("Agreement: not agreed yet")
        if not parts and call.transcript:
            latest = call.transcript[-1].text
            parts.append(f"Latest message: {latest}")
        return ". ".join(parts) if parts else "No conversation captured yet."

    def _read(self) -> dict[str, Any]:
        if not self.store_path.exists():
            return {"calls": {}}
        return json.loads(self.store_path.read_text(encoding="utf-8-sig"))

    def _write(self, data: dict[str, Any]) -> None:
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.data_dir) as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            temp_path = Path(tmp.name)
        temp_path.replace(self.store_path)

    def _upsert_file_call(self, call: StoredCall) -> None:
        data = self._read()
        data.setdefault("calls", {})[call.id] = call.model_dump(mode="json")
        self._write(data)

    def _upsert_supabase_call(self, call: StoredCall) -> None:
        call_data = call.model_dump(mode="json")
        self._supabase_request(
            "POST",
            "/rest/v1/rubi_calls?on_conflict=id",
            json={
                "id": call.id,
                "provider_call_id": call.provider_call_id,
                "from_number": call.from_number,
                "to_number": call.to_number,
                "created_at": call_data["created_at"],
                "updated_at": call_data["updated_at"],
                "call_data": call_data,
            },
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        )

    def _supabase_request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        request_headers = {
            "apikey": self.supabase_key or "",
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
            **(headers or {}),
        }
        with httpx.Client(timeout=15) as client:
            response = client.request(
                method,
                f"{self.supabase_url}{path}",
                json=json,
                headers=request_headers,
            )
        response.raise_for_status()
        if not response.content:
            return []
        return response.json()

    def _migrate_local_calls_to_supabase(self) -> None:
        if not self.supabase_enabled or not self.store_path.exists():
            return
        try:
            local_calls = [
                StoredCall.model_validate(call)
                for call in self._read().get("calls", {}).values()
            ]
            for call in local_calls:
                self._upsert_supabase_call(call)
        except (httpx.HTTPError, ValueError, KeyError):
            return

    def _data_dir(self) -> Path:
        if settings.rubi_data_dir:
            return Path(settings.rubi_data_dir)
        if "pytest" in sys.modules:
            return Path(__file__).resolve().parents[3] / ".pytest_cache" / "rubi-data"
        if os.environ.get("VERCEL"):
            return Path("/tmp/rubi-data")
        return Path(__file__).resolve().parents[3] / "data"


storage_service = StorageService()
