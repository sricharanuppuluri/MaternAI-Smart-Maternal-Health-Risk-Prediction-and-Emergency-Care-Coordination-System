"""Application configuration settings for MaternAI Backend."""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Safe application settings handling environment variables.
    
    All external credentials and services are optional by default to allow
    local development, testing, and continuous integration to run without secrets.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General Project Metadata
    PROJECT_NAME: str = "MaternAI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Supabase Configuration (Server-side only; never expose key to frontend)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # ML Model Configuration (Screening / Decision Support)
    MODEL_PATH: str = "ml/models/maternai_risk_model.joblib"
    MODEL_VERSION: str = "v0.1.0"

    # Local LLM Service (Ollama / Local Inference)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    @property
    def is_supabase_configured(self) -> bool:
        """Check if Supabase credentials are configured."""
        return bool(self.SUPABASE_URL and self.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
