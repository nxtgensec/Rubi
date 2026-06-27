from app.api.v1.routers import (
    agents,
    auth,
    calls,
    events,
    knowledge,
    metrics,
    telephony,
    tools,
    twilio,
    visits,
)
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(telephony.router, prefix="/telephony", tags=["telephony"])
api_router.include_router(twilio.router, prefix="/twilio", tags=["twilio"])
api_router.include_router(visits.router, prefix="/visits", tags=["visits"])
