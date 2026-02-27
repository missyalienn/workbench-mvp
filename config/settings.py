from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Project-wide settings and configuration."""

    # Logging
    LOG_LEVEL: str = Field(
        "INFO",
        validation_alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    LOG_FORMAT: str = Field(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        validation_alias="LOG_FORMAT",
        description="Logging format (%(asctime)s [%(levelname)s] %(name)s: %(message)s)",
    )
    LOG_DATE_FORMAT: str = Field(
        "%H:%M:%S",
        validation_alias="LOG_DATE_FORMAT",
        description="Logging date format (%%H:%%M:%%S)",
    )
    LOG_FORMAT_TYPE: str = Field(
        "text",
        validation_alias="LOG_FORMAT_TYPE",
        description="Log output: 'text' or 'json'",
    )

    # HTTP Retry Defaults
    RETRY_MAX_ATTEMPTS: int = Field(
        3,
        validation_alias="RETRY_MAX_ATTEMPTS",
        description="Maximum number of retry attempts",
    ) 
    RETRY_WAIT_MULTIPLIER: int = Field(
        1,
        validation_alias="RETRY_WAIT_MULTIPLIER",
        description="Multiplier for the wait time between retry attempts",
    )
    RETRY_WAIT_MAX: int = Field(
        15,
        validation_alias="RETRY_WAIT_MAX",
        description="Maximum wait time between retry attempts",
    )    
  

    # Agent Planner Defaults
    ALLOWED_SUBREDDITS: list[str] = [
        "diy",
        "homeimprovement",
        #"homemaintenance",
        #"homeowners", 
        "fixit",
        "plumbing",
        "askelectricians",
        "howto",
        "homedecorating",
        "diyuk",
        "hvacadvice"
    ]
    DEFAULT_SUBREDDITS: list[str] = []
    MAX_SUBREDDITS: int = 3
    MAX_SEARCH_TERMS: int = 5

    #Multithreading Configuration
    FETCHER_MAX_WORKERS: int = 3
    FETCHER_ENABLE_CONCURRENCY: bool = True

    # Semantic Ranking Configuration
    USE_SEMANTIC_RANKING: bool = Field(
        False,
        validation_alias="USE_SEMANTIC_RANKING",
        description="Enable semantic ranking (embeddings + cosine similarity)",
    )
    EMBEDDING_MODEL: str = Field(
        "text-embedding-3-small",
        validation_alias="EMBEDDING_MODEL",
        description="Embedding model name",
    )
    EMBEDDING_CACHE_PATH: str = Field(
        "data/embedding_cache.sqlite3",
        validation_alias="EMBEDDING_CACHE_PATH",
        description="SQLite path for embedding cache",
    )
    MAX_EMBED_TEXT_CHARS: int = Field(
        4000,
        validation_alias="MAX_EMBED_TEXT_CHARS",
        description="Max characters for embedding input text",
    )
    VECTOR_STORE_TYPE: str = Field(
        "sqlite",
        validation_alias="VECTOR_STORE_TYPE",
        description="Vector store backend type (e.g., sqlite, pinecone)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
