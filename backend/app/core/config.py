"""
Application configuration and settings.
"""

import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Employee Onboarding Workflow Automator"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise AI-powered HR onboarding automation platform"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # API
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@localhost:5432/onboarding_db"
    )
    DB_SSL_REQUIRE: bool = os.getenv("DB_SSL_REQUIRE", "true").lower() == "true"
    DB_CONNECT_TIMEOUT: int = int(os.getenv("DB_CONNECT_TIMEOUT", "15"))
    DB_COMMAND_TIMEOUT: int = int(os.getenv("DB_COMMAND_TIMEOUT", "30"))
    DB_SOCKET_TIMEOUT: int = int(os.getenv("DB_SOCKET_TIMEOUT", "5"))
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "8"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "45"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "600"))

    # JWT Configuration
    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_EXPIRATION_HOURS: int = 24
    ACCESS_TOKEN_EXPIRE_TIMEDELTA: timedelta = timedelta(hours=JWT_EXPIRATION_HOURS)
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    # Password
    PASSWORD_MIN_LENGTH: int = 8

    # LiteLLM Configuration
    LITELLM_PROXY_URL: str = os.getenv("LITELLM_PROXY_URL", "https://litellm.amzur.com")
    LITELLM_API_KEY: str = os.getenv("LITELLM_API_KEY", "")

    # ChromaDB Configuration
    CHROMADB_HOST: str = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT: int = int(os.getenv("CHROMADB_PORT", "8001"))
    CHROMADB_COLLECTION_PREFIX: str = "onboarding"

    # File Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_UPLOAD_EXTENSIONS: list[str] = ["pdf", "docx", "txt", "jpg", "jpeg", "png"]
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Email Configuration (placeholder for future email service)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_ENABLED: bool = os.getenv("SMTP_ENABLED", "false").lower() == "true"
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "noreply@onboarding.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Onboarding Platform")

    # OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/google/callback")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    class Config:
        env_file = str(Path(__file__).resolve().parents[2] / ".env")
        case_sensitive = True
        extra = "ignore"

    def resolved_database_url(self) -> str:
        """Single source of truth for DB connectivity."""
        database_url = self.DATABASE_URL.strip()

        # Recover from a common misconfiguration where both SQLAlchemy and
        # libpq schemes are accidentally prepended.
        if database_url.startswith("postgresql+asyncpg://postgresql://"):
            return database_url.replace("postgresql+asyncpg://postgresql://", "postgresql+asyncpg://", 1)

        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return database_url

    def validate_database_url(self) -> None:
        """Fail fast for invalid DB URL configuration at startup."""
        parsed = urlparse(self.resolved_database_url())
        if parsed.scheme != "postgresql+asyncpg":
            raise ValueError(
                "Invalid DATABASE_URL scheme. Use postgresql+asyncpg:// (or postgresql:// which is auto-normalized)."
            )
        if not parsed.hostname:
            raise ValueError("Invalid DATABASE_URL: host is missing.")
        if not parsed.path or parsed.path == "/":
            raise ValueError("Invalid DATABASE_URL: database name is missing.")

        placeholder_passwords = {
            "your_password",
            "your-password",
            "change_me",
            "changeme",
            "password",
        }
        parsed_password = (parsed.password or "").lower()
        if parsed_password in placeholder_passwords:
            raise ValueError(
                "Invalid DATABASE_URL: placeholder password detected. Replace with real Supabase DB password."
            )

    def database_target(self) -> tuple[str, int, str]:
        parsed = urlparse(self.resolved_database_url())
        return (
            parsed.hostname or "unknown",
            parsed.port or 5432,
            parsed.path.lstrip("/") or "postgres",
        )

    def using_supabase(self) -> bool:
        host, _, _ = self.database_target()
        return host.endswith((".supabase.co", ".supabase.com"))


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
