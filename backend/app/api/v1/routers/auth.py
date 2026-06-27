from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse
from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    if not payload.email or not payload.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login")
    return TokenResponse(access_token=create_access_token(subject=payload.email))
