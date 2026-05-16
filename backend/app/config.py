from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = f"sqlite:///{BACKEND_ROOT / 'data' / 'penguwave.db'}"
    cors_origins: str = "http://localhost:5173"
    cookie_secure: bool = False
    cookie_name: str = "sid"
    session_ttl_hours: int = 24
    admin_email: str = "admin@penguwave.io"
    admin_bootstrap_password: str | None = None
    environment: str = "development"  # set to "test" in pytest to disable rate limits
    mock_events_path: Path = REPO_ROOT / "data" / "mock_events.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
