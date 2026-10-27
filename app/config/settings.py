"""Env-only settings for the V2 ingest stack (no keychain/SSM; secrets come from the environment)."""

from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    # Logging
    LOG_LEVEL: str = Field("INFO", description="DEBUG, INFO, WARNING, ERROR")
    LOG_FORMAT_TYPE: str = Field("text", description="'text' or 'json'")

    # Retry
    RETRY_MAX_ATTEMPTS: int = Field(3, ge=1)
    RETRY_WAIT_MULTIPLIER: int = Field(1, ge=0)
    RETRY_WAIT_MAX: int = Field(15, ge=0)

    # Reddit (optional at import time; the client raises AuthError when missing)
    REDDIT_CLIENT_ID: SecretStr | None = None
    REDDIT_CLIENT_SECRET: SecretStr | None = None
    REDDIT_USER_AGENT: str | None = None

    # Embeddings / vector store
    OPENAI_API_KEY: SecretStr | None = None
    PINECONE_API_KEY: SecretStr | None = None
    PINECONE_INDEX: str = "workbench-oai-te3s-1536"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Chunking
    CHUNK_SIZE: int = Field(1000, gt=0)
    CHUNK_OVERLAP: int = Field(150, ge=0)


settings = Settings()
