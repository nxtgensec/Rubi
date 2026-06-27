import httpx
from app.schemas.visit import VisitCreate, VisitStats
from app.services.visitor_service import SupabaseNotConfiguredError, visitor_service
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("", response_model=VisitStats)
async def get_visit_stats() -> VisitStats:
    try:
        return await visitor_service.get_stats()
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=exc.response.text) from exc


@router.post("", response_model=VisitStats)
async def record_visit(payload: VisitCreate) -> VisitStats:
    try:
        return await visitor_service.record_visit(payload.visitor_id, payload.user_agent)
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=exc.response.text) from exc
