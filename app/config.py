import json
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors_origins(value: Optional[str] | None) -> List[str]:
    """Parse BACKEND_CORS_ORIGINS from environment.

    Accepts JSON list like '["https://example.com"]' or comma-separated string
    like 'https://example.com,https://app.local'. Returns a list of origins.
    """
    if not value:
        return []
    value = value.strip()
    # Try JSON first
    if value.startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed]
        except Exception:
            pass
    # Fallback comma-separated
    return [x.strip() for x in value.split(",") if x.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/cow_db"
    PROJECT_NAME: str = "Cow Monitoring API"
    VERSION: str = "0.1.0"

    # CORS origins can be a JSON list or comma-separated string
    BACKEND_CORS_ORIGINS: Optional[str] = None

    @property
    def cors_origins(self) -> List[str]:
        parsed = _parse_cors_origins(self.BACKEND_CORS_ORIGINS)
        return parsed if parsed else ["*"]


settings = Settings()
