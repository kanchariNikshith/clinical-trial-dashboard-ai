"""Application settings and configuration."""

from typing import List, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Clinical Trial Dashboard"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    API_BASE_URL: str = "http://localhost:8000"

    # PostgreSQL is the required runtime database; test runs must also point at PostgreSQL explicitly.
    DATABASE_URL: str = "postgresql+psycopg://clinical_app:clinical_app@localhost:5432/clinical_trials"
    TEST_DATABASE_URL: str = ""

    # JWT
    JWT_SECRET_KEY: str = "development_secret_key_change_in_production_min32chars"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # Session cookies
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAME_SITE: str = "lax"

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

    @model_validator(mode="after")
    def validate_runtime_settings(self) -> "Settings":
        env_name = self.APP_ENV.lower()

        if env_name == "production" and len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production.")

        default_secret_values = {
            "development_secret_key_change_in_production_min32chars",
            "replace_with_a_long_random_secret",
        }
        if env_name == "production" and self.JWT_SECRET_KEY in default_secret_values:
            raise ValueError("Production requires a non-default JWT_SECRET_KEY.")

        if env_name == "testing":
            if not self.TEST_DATABASE_URL:
                raise ValueError(
                    "TEST_DATABASE_URL must be set to an explicit PostgreSQL URL when APP_ENV=testing. "
                    "SQLite fallback is not allowed."
                )
            if self.TEST_DATABASE_URL.startswith("sqlite"):
                raise ValueError(
                    "SQLite database URLs are not allowed in APP_ENV=testing. "
                    "Configure a PostgreSQL TEST_DATABASE_URL instead."
                )
            return self

        if self.DATABASE_URL.startswith("sqlite"):
            raise ValueError(
                "SQLite database URLs are not supported for the application runtime. "
                "Configure a PostgreSQL DATABASE_URL instead."
            )

        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL is required. Configure it in the environment or .env file.")

        return self

    @property
    def effective_database_url(self) -> str:
        if self.APP_ENV.lower() == "testing" and self.TEST_DATABASE_URL:
            return self.TEST_DATABASE_URL
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
