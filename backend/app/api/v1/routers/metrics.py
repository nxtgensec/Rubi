from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def metrics() -> dict[str, int | float]:
    return {
        "active_calls": 1,
        "average_latency_ms": 480,
        "calls_today": 24,
        "tool_success_rate": 96.4,
    }
