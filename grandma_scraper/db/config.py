"""
Database configuration.

Loads database settings from environment variables.
"""

import os
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    # PostgreSQL connection
    postgres_user: str = "grandma_scraper"
    postgres_password: str = "scraper_password"
    postgres_server: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "grandma_scraper"

    # SQLite fallback for development
    use_sqlite: bool = False
    sqlite_path: str = "grandma_scraper.db"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = DatabaseSettings()


def get_database_url() -> str:
    """
    Get database connection URL.

    Returns:
        SQLAlchemy database URL string

    Environment Variables:
        USE_SQLITE: Set to 'true' to use SQLite instead of PostgreSQL
        POSTGRES_USER: PostgreSQL username
        POSTGRES_PASSWORD: PostgreSQL password
        POSTGRES_SERVER: PostgreSQL server hostname
        POSTGRES_PORT: PostgreSQL port
        POSTGRES_DB: Database name
    """
    if settings.use_sqlite:
        return f"sqlite:///{settings.sqlite_path}"

    return (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_server}:{settings.postgres_port}/{settings.postgres_db}"
    )
