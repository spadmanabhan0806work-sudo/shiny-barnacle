from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = Field(
        default="postgresql+asyncpg://operyx:operyx@localhost:5432/operyx",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql://operyx:operyx@localhost:5432/operyx",
        alias="DATABASE_URL_SYNC",
    )
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_path: str = Field(default="./data/uploads", alias="STORAGE_LOCAL_PATH")
    stt_provider: str = Field(default="mock", alias="STT_PROVIDER")
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")
    google_api_key: str = Field(
        default="",
        alias="GOOGLE_API_KEY",
    )
    whisperx_enabled: bool = Field(default=False, alias="WHISPERX_ENABLED")
    tenant_id: str = Field(default="default", alias="TENANT_ID")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    auth_enabled: bool = Field(default=False, alias="AUTH_ENABLED")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")

    yaml_config: dict[str, Any] = Field(default_factory=dict, exclude=True)

    def load_yaml(self, config_path: Path | None = None) -> None:
        path = config_path or Path("config/default.yaml")
        if path.exists():
            with open(path, encoding="utf-8") as f:
                self.yaml_config = yaml.safe_load(f) or {}
        auth = self.yaml_config.setdefault("auth", {})
        if self.auth_enabled:
            auth["enabled"] = True

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value: Any = self.yaml_config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.load_yaml()
    return settings
