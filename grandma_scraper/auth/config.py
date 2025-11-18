"""
Authentication configuration.

Loads authentication settings from environment variables.
"""

import os
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Authentication configuration settings."""

    # JWT settings
    secret_key: str = os.getenv(
        "SECRET_KEY",
        "your-secret-key-change-this-in-production-make-it-long-and-random",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


_settings: AuthSettings | None = None


def get_auth_settings() -> AuthSettings:
    """Get cached authentication settings."""
    global _settings
    if _settings is None:
        _settings = AuthSettings()
    return _settings
