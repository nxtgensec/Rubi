import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    jwt_secret: str = Field(default="change-me-in-production")
    database_url: str = "postgresql+asyncpg://rubi:rubi@localhost:5432/rubi"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    public_backend_url: str = "https://your-public-rubi-domain.example"
    public_voice_stream_base_url: str = "wss://your-public-rubi-domain.example/voice"
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_phone_number: str | None = None
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_secret_key: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_access_token: str | None = None
    cors_origins: str = '["http://localhost:3000","http://127.0.0.1:3000"]'
    rubi_data_dir: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        value = self.cors_origins.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
        except json.JSONDecodeError:
            pass
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
