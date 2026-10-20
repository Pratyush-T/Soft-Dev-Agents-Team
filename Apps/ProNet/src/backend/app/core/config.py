"""Configuration management using Pydantic Settings."""
import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment or defaults."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application Metadata
    PRONET_ENV: str = Field(default="development", description="development | production | test")
    PRONET_HOST: str = Field(default="127.0.0.1", description="Application bind address")
    PRONET_PORT: int = Field(default=8000, description="Application bind port")
    PRONET_CLIENT_ORIGIN: str = Field(default="http://localhost:5173", description="Allowed CORS origin")

    # Cryptographic & Security Keys
    PRONET_JWT_SECRET_KEY: str = Field(
        default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        description="256-bit cryptographic secret for signing authentication tokens"
    )
    PRONET_JWT_ALGORITHM: str = Field(default="HS256")
    PRONET_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)  # 24 hours

    # Storage & Database Configuration
    PRONET_DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./pronet.db",
        description="Async SQLite connection string"
    )
    PRONET_SQLITE_BUSY_TIMEOUT_MS: int = Field(default=5000)
    PRONET_UPLOAD_DIR: str = Field(default="./uploads")

    # Performance & Payload Thresholds
    PRONET_MAX_AVATAR_BYTES: int = Field(default=2 * 1024 * 1024)   # 2 MB
    PRONET_MAX_POST_MEDIA_BYTES: int = Field(default=5 * 1024 * 1024) # 5 MB
    PRONET_MAX_RESUME_BYTES: int = Field(default=5 * 1024 * 1024)     # 5 MB


@lru_cache()
def get_settings() -> Settings:
    """Return singleton instance of application settings."""
    return Settings()


settings = get_settings()
