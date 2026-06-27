from app.schemas.call import CallRead
from app.services.storage_service import storage_service


class CallService:
    async def list_calls(self) -> list[CallRead]:
        calls = []
        for call in storage_service.list_calls():
            if call.lead.agreed is True:
                sentiment = "agreed"
            elif call.lead.agreed is False:
                sentiment = "not_agreed"
            else:
                sentiment = "pending"

            calls.append(
                CallRead(
                    id=call.id,
                    caller=call.from_number,
                    language=call.language,
                    agent_id="agent_default",
                    duration_seconds=0,
                    status=call.lead.status,
                    recording_status=call.recording_status,
                    recording_url=call.recording_url,
                    summary=call.summary,
                    transcript=[f"{turn.role}: {turn.text}" for turn in call.transcript],
                    sentiment=sentiment,
                    started_at=call.created_at,
                )
            )
        return calls


call_service = CallService()
