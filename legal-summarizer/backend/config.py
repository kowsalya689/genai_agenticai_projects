"""Central configuration. Every value can be overridden with an environment variable or a .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    # ---- app ----
    app_name: str = "LexBrief Legal Summarizer"
    version: str = "1.0.0"
    environment: str = "development"          # development | production
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    # ---- model ----
    model_dir: str = str(ROOT / "model" / "bart_legal_final")   # fine-tuned folder from the notebook (section 14)
    fallback_model: str = "facebook/bart-large-cnn"             # used if model_dir does not exist
    device: str = "auto"                                        # auto | cpu | cuda
    preload_model: bool = True                                  # load at start-up instead of on first request

    # ---- summarisation pipeline (same defaults as the notebook) ----
    max_source_tokens: int = 1024
    chunk_tokens: int = 900
    target_compression: float = 0.20
    final_cap_tokens: int = 350
    max_levels: int = 3
    num_beams: int = 4

    # ---- request limits / headers ----
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"   # comma-separated, or "*"
    max_upload_mb: int = 5
    max_chars: int = 400_000
    rate_limit_per_minute: int = 30            # per client IP on summarise/extract, 0 disables

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
