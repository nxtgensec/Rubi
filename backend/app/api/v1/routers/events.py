import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


async def demo_event_stream():
    events = [
        {"type": "CallStarted", "call_id": "call_demo_001"},
        {"type": "TranscriptReceived", "text": "Namaskaram, appointment kavala?"},
        {"type": "LLMCompleted", "latency_ms": 420},
    ]
    for event in events:
        yield f"data: {json.dumps(event)}\n\n"
        await asyncio.sleep(1)


@router.get("/stream")
async def stream_events() -> StreamingResponse:
    return StreamingResponse(demo_event_stream(), media_type="text/event-stream")
