"""
Authentication configuration.

Loads authentication settings from environment variables.
"""

import os
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Authentication configuration settings."""

    # JWT settings
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.secret_key or len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY environment variable must be set and at least 32 characters long"
            )

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
