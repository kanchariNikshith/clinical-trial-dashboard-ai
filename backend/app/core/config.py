"""Application settings and configuration."""

from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Clinical Trial Dashboard"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    API_BASE_URL: str = "http://localhost:8000"

    # Database: default to local sqlite fallback if not configured
    DATABASE_URL: str = "sqlite:///./dev.db"

    # JWT
    JWT_SECRET_KEY: str = "development_secret_key_change_in_production_min32chars"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_ALGORITHM: str = "HS256"

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Upload constraints
    MAX_UPLOAD_MB: int = 10
    MAX_CSV_ROWS: int = 10000

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173"]

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
