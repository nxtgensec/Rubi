import json
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from app.schemas.intake import LeadDetails, StoredCall, StoredTranscriptTurn


class StorageService:
    def __init__(self) -> None:
        self.data_dir = Path(__file__).resolve().parents[3] / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.store_path = self.data_dir / "rubi_store.json"

    def list_calls(self) -> list[StoredCall]:
        data = self._read()
        calls = [StoredCall.model_validate(call) for call in data.get("calls", {}).values()]
        return sorted(calls, key=lambda call: call.created_at, reverse=True)

    def get_call(self, call_id: str) -> StoredCall | None:
        data = self._read()
        raw = data.get("calls", {}).get(call_id)
        return StoredCall.model_validate(raw) if raw else None

    def get_call_by_provider_id(self, provider_call_id: str) -> StoredCall | None:
        for call in self.list_calls():
            if call.provider_call_id == provider_call_id:
                return call
        return None

    def upsert_call(self, call: StoredCall) -> StoredCall:
        data = self._read()
        call.updated_at = datetime.now(UTC)
        data.setdefault("calls", {})[call.id] = call.model_dump(mode="json")
        self._write(data)
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
        if lead.budget:
            parts.append(f"Budget: {lead.budget}")
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
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.data_dir) as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            temp_path = Path(tmp.name)
        temp_path.replace(self.store_path)


storage_service = StorageService()
