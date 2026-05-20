from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    database_url: str

    telegram_bot_token: str | None

    scheduler_control_base_url: str
    scheduler_control_base_port: int

    serper_api_key: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        scheduler_control_base_port=int(os.getenv("SCHEDULER_CONTROL_BASE_PORT", 8000))
    
        return cls(
            app_name=os.getenv("APP_NAME", "health-agent"),
            database_url=os.getenv(
                "DATABASE_URL",
                "sqlite+aiosqlite:///./data/health_agent.db",
            ),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            scheduler_control_base_url=f"http://127.0.0.1:{scheduler_control_base_port}",
            scheduler_control_base_port=scheduler_control_base_port,
            
            serper_api_key=os.getenv("SERPER_API_KEY"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()