from contextlib import asynccontextmanager
from pathlib import Path
import sys

backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.services.media_stream_service import media_stream_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title="Rubi API",
    description="API for the Rubi AI Voice Employee platform.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "rubi-backend"}


@app.websocket("/voice/{call_id}")
async def twilio_voice_stream(call_id: str, websocket: WebSocket) -> None:
    try:
        await media_stream_service.handle_twilio_stream(call_id, websocket)
    except WebSocketDisconnect:
        return
