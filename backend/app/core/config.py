from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "NEUROFLOW AI"
    APP_ENV: str = "development"
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    DATABASE_URL: str
    CREDENTIAL_ENCRYPTION_KEY: str
    PUBLIC_API_BASE_URL: str = "http://localhost:8000"
    PUBLIC_FRONTEND_URL: str = "http://localhost:5173"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/youtube/oauth/callback"
    MEDIA_WORK_DIR: str = "/tmp/neuroflow_work"
    BLENDER_BINARY_PATH: str = "blender"
    FFMPEG_BINARY_PATH: str = "ffmpeg"
    WHISPER_MODEL_SIZE: str = "base"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
