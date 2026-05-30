"""Application settings loaded from .env."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    database_type: str = "sqlite"
    sqlite_path: str = str(_BACKEND_DIR / "task_reminder.db")

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3307
    mysql_user: str = "root"
    mysql_password: str = "taskreminder"
    mysql_database: str = "task_reminder"

    scheduler_interval_seconds: int = 30
    dingding_webhook: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:
        if self.database_type.lower() == "sqlite":
            path = Path(self.sqlite_path)
            if not path.is_absolute():
                path = _BACKEND_DIR / path
            return f"sqlite:///{path.as_posix()}"
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )


settings = Settings()
