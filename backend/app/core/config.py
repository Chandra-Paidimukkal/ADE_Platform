"""Application-wide settings loaded from environment / .env file."""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "ADE Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Paths
    DATA_DIR: Path = Path("backend/data")
    PDF_DIR:  Path = Path("backend/data/pdfs")
    OUTPUT_DIR: Path = Path("backend/data/outputs")
    SCHEMA_DIR: Path = Path("backend/data/schemas")

    # AI
    AI_PROVIDER: str = "anthropic"   # openai | anthropic | gemini | ollama | landingai | custom | none

    OPENAI_API_KEY:  str = ""
    OPENAI_MODEL:    str = "gpt-4o"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL:   str = "claude-opus-4-6"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL:   str = "gemini-1.5-pro"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL:    str = "llama3"

    LANDINGAI_API_KEY:  str = ""
    LANDINGAI_ENDPOINT: str = ""

    BATCH_MAX_WORKERS:      int = 4
    BATCH_TIMEOUT_PER_FILE: int = 120

    AI_REQUEST_TIMEOUT: int = 60
    AI_MAX_RETRIES:     int = 2

    def ensure_dirs(self) -> None:
        for p in (self.PDF_DIR, self.OUTPUT_DIR, self.SCHEMA_DIR):
            Path(p).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
