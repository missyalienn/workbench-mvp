from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Project-wide settings and configuration."""

    # Logging
    LOG_LEVEL: str = Field(
        ...,
        validation_alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    LOG_FORMAT: str = Field(
        ...,
        validation_alias="LOG_FORMAT",
        description="Logging format (%(asctime)s [%(levelname)s] %(name)s: %(message)s)",
    )
    LOG_DATE_FORMAT: str = Field(
        ...,
        validation_alias="LOG_DATE_FORMAT",
        description="Logging date format (%%H:%%M:%%S)",
    )
    LOG_FORMAT_TYPE: str = Field(
        "text",
        validation_alias="LOG_FORMAT_TYPE",
        description="Log output: 'text' or 'json'",
    )

    # Agent Planner Defaults 
    ALLOWED_SUBREDDITS: list[str] = ["diy", "homeimprovement", "woodworking"]
    DEFAULT_SUBREDDITS: list[str] = ["diy"]
    MAX_SUBREDDITS: int = 3
    MAX_SEARCH_TERMS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
        
settings = Settings()
