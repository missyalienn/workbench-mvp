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
    ALLOWED_SUBREDDITS: list[str] = ["diy", "homeimprovement", "woodworking"]
    DEFAULT_SUBREDDITS: list[str] = ["diy"]
    MAX_SUBREDDITS: int = 3
    MAX_SEARCH_TERMS: int = 5

    #Multithreading Configuration
    FETCHER_MAX_WORKERS: int = 3
    FETCHER_ENABLE_CONCURRENCY: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
