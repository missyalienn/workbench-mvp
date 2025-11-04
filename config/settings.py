from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Project-wide settings and configuration."""

    # Logging
    LOG_LEVEL: str = Field(..., env="LOG_LEVEL", description="Logging level (DEBUG, INFO, WARNING, ERROR)")
    LOG_FORMAT: str = Field(..., env="LOG_FORMAT", description="Logging format (%(asctime)s [%(levelname)s] %(name)s: %(message)s)")
    LOG_DATE_FORMAT: str = Field(..., env="LOG_DATE_FORMAT", description="Logging date format (%%H:%%M:%%S)")

    # Agent Planner Defaults 
    ALLOWED_SUBREDDITS: list[str] = ["diy", "homeimprovement", "woodworking"]
    DEFAULT_SUBREDDITS: list[str] = ["diy"]
    MAX_SUBREDDITS: int = 3
    MAX_SEARCH_TERMS: int = 5


class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"

settings = Settings()