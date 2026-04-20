from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    data_dir: Path = Path(os.getenv("JD_MONITOR_DATA_DIR", "./data"))
    database_name: str = "monitor.db"
    log_name: str = "app.log"
    host: str = "0.0.0.0"
    port: int = 8080
    app_name: str = "JDownloader Monitor"
    app_url: str = "http://localhost:8080"
    secret_key: str = "development-secret"

    model_config = SettingsConfigDict(
        env_prefix="JD_MONITOR_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        return self.data_dir / self.database_name

    @property
    def log_path(self) -> Path:
        return self.data_dir / self.log_name

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


settings = RuntimeSettings()
