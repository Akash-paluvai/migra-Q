import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Migra-Q"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173

    DATABASE_URL: str = "sqlite:///./migraq.db"
    DUCKDB_MEMORY_LIMIT: str = "2GB"
    DUCKDB_THREADS: int = 4

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    SECRET_KEY: str = "migraq-secret-key-change-in-production"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    MIN_ASSURANCE_SCORE_PASS: float = 85.0
    MAX_ROW_DIFF_TOLERANCE: float = 0.0001

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
