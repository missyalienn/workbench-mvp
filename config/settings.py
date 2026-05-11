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

    # OpenAI Authentication
    OPENAI_USE_KEYCHAIN: bool = Field(
        True,
        validation_alias="OPENAI_USE_KEYCHAIN",
        description="Use system keychain for OpenAI credentials instead of env vars",
    )
    OPENAI_API_KEY: str | None = Field(
        None,
        validation_alias="OPENAI_API_KEY",
        description="OpenAI API key used when keychain auth is disabled",
    )
    OPENAI_API_KEY_SSM_PARAMETER: str | None = Field(
        None,
        validation_alias="OPENAI_API_KEY_SSM_PARAMETER",
        description="SSM parameter name for the OpenAI API key in production",
    )
    OPENAI_KEYCHAIN_SERVICE: str = Field(
        "openai-key",
        validation_alias="OPENAI_KEYCHAIN_SERVICE",
        description="Keychain service name for the OpenAI API key",
    )
    OPENAI_KEYCHAIN_LABEL: str = Field(
        "openai-dev",
        validation_alias="OPENAI_KEYCHAIN_LABEL",
        description="Keychain label for the OpenAI API key",
    )

    # Reddit Authentication
    REDDIT_USE_KEYCHAIN: bool = Field(
        True,
        validation_alias="REDDIT_USE_KEYCHAIN",
        description="Use system keychain for Reddit credentials instead of env vars",
    )
    REDDIT_CLIENT_ID: str | None = Field(
        None,
        validation_alias="REDDIT_CLIENT_ID",
        description="Reddit client ID used when keychain auth is disabled",
    )
    REDDIT_CLIENT_ID_SSM_PARAMETER: str | None = Field(
        None,
        validation_alias="REDDIT_CLIENT_ID_SSM_PARAMETER",
        description="SSM parameter name for the Reddit client ID in production",
    )
    REDDIT_CLIENT_SECRET: str | None = Field(
        None,
        validation_alias="REDDIT_CLIENT_SECRET",
        description="Reddit client secret used when keychain auth is disabled",
    )
    REDDIT_CLIENT_SECRET_SSM_PARAMETER: str | None = Field(
        None,
        validation_alias="REDDIT_CLIENT_SECRET_SSM_PARAMETER",
        description="SSM parameter name for the Reddit client secret in production",
    )
    REDDIT_USER_AGENT: str = Field(
        "Workbench/1.0 by /u/chippetto90",
        validation_alias="REDDIT_USER_AGENT",
        description="User-Agent header for Reddit API requests",
    )
    REDDIT_USER_AGENT_SSM_PARAMETER: str | None = Field(
        None,
        validation_alias="REDDIT_USER_AGENT_SSM_PARAMETER",
        description="SSM parameter name for the Reddit user agent in production",
    )
    REDDIT_CLIENT_ID_SERVICE: str = Field(
        "reddit-client-id",
        validation_alias="REDDIT_CLIENT_ID_SERVICE",
        description="Keychain service name for the Reddit client ID",
    )
    REDDIT_CLIENT_SECRET_SERVICE: str = Field(
        "reddit-client-secret",
        validation_alias="REDDIT_CLIENT_SECRET_SERVICE",
        description="Keychain service name for the Reddit client secret",
    )
    REDDIT_USER_AGENT_SERVICE: str = Field(
        "reddit-user-agent",
        validation_alias="REDDIT_USER_AGENT_SERVICE",
        description="Keychain service name for the Reddit user agent",
    )
    REDDIT_KEYCHAIN_LABEL: str = Field(
        "reddit-dev",
        validation_alias="REDDIT_KEYCHAIN_LABEL",
        description="Keychain label for Reddit credentials",
    )

    # Internal Proxy Authentication
    PROXY_TOKEN: str | None = Field(
        None,
        validation_alias="PROXY_TOKEN",
        description="Shared token used to authorize server-side proxy requests",
    )
    PROXY_TOKEN_SSM_PARAMETER: str | None = Field(
        None,
        validation_alias="PROXY_TOKEN_SSM_PARAMETER",
        description="SSM parameter name for the shared proxy token in production",
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
  

    # Planner Agent Defaults
    ALLOWED_SUBREDDITS: list[str] = [
        "diy",
        "homeimprovement",
        #"homemaintenance",
        #"homeowners", 
        "fixit",
        "plumbing",
        "woodworking",
        "howto",
        "homedecorating",
        "diyuk",
        "hvacadvice"
    ]
    DEFAULT_SUBREDDITS: list[str] = []
    MAX_SUBREDDITS: int = 3
    MAX_SEARCH_TERMS: int = 5

    FETCHER_MAX_COMMENTS_PER_POST: int = Field(
        5,
        validation_alias="FETCHER_MAX_COMMENTS_PER_POST",
        description=(
            "Fetch-time cap on comments retained per post after quality filtering. "
            "Distinct from ContextBuilderConfig.max_comments_per_post, which further limits "
            "how many comment excerpts are included in the LLM payload."
        ),
    )

    # Semantic Ranking Configuration
    USE_SEMANTIC_RANKING: bool = Field(
        True,
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
