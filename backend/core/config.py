"""Typed application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — all values come from environment / .env file."""

    APP_ENV: str = "development"
    APP_NAME: str = "migra-q"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    DATABASE_URL: str = "postgresql+psycopg://migraq:migraq@localhost:5432/migraq"
    PERSISTENCE_MODE: str = "postgres"  # "postgres" or "memory" (test mode only)

    # Generative AI / LLM Translation Engine Configuration
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_RETRIES: int = 2
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_OUTPUT_TOKENS: int = 6000
    LOG_TRANSLATION_SQL: bool = False

    PROMPT_VERSION: str = "0.1.0"
    TRANSLATOR_VERSION: str = "0.1.0"

    LOG_LEVEL: str = "INFO"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_persistence_policy(self) -> None:
        """Enforce PostgreSQL persistence policy outside TEST environment."""
        if (
            self.APP_ENV in ("development", "demo", "production")
            and self.PERSISTENCE_MODE != "postgres"
        ):
            raise ValueError(
                f"Invalid PERSISTENCE_MODE='{self.PERSISTENCE_MODE}' for APP_ENV='{self.APP_ENV}'. "
                "PostgreSQL is mandatory for non-test environments."
            )

    def validate_llm_config(self) -> None:
        """Validate LLM configuration parameters."""
        if self.LLM_PROVIDER in ("openai", "openrouter"):
            if not self.LLM_MODEL:
                raise ValueError(f"LLM_MODEL must be configured when LLM_PROVIDER is '{self.LLM_PROVIDER}'.")
            if not self.LLM_API_KEY:
                raise ValueError(f"LLM_API_KEY must be configured when LLM_PROVIDER is '{self.LLM_PROVIDER}'.")


settings = Settings()
