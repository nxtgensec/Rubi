from datetime import UTC, datetime, timedelta

from app.core.config import settings
from jose import jwt

ALGORITHM = "HS256"


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expires_at = datetime.now(UTC) + (expires_delta or timedelta(hours=8))
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
