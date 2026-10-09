"""Application configuration and environment settings."""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Support Intent Observatory."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    app_name: str = "Support Intent Observatory"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = False

    # Demo mode settings
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")

    # Persistent SQLite Database
    database_url: str = Field(
        default="sqlite:///./data/observatory.db",
        alias="DATABASE_URL",
    )

    # OIDC / Keycloak Configuration
    oidc_issuer_url: str = Field(
        default="http://127.0.0.1:8080/realms/support-observatory",
        alias="OIDC_ISSUER_URL",
    )
    oidc_client_id: str = Field(
        default="support-observatory-client",
        alias="OIDC_CLIENT_ID",
    )
    oidc_client_secret: Optional[str] = Field(
        default=None,
        alias="OIDC_CLIENT_SECRET",
    )
    oidc_audience: str = Field(
        default="support-observatory-client",
        alias="OIDC_AUDIENCE",
    )
    oidc_redirect_uri: str = Field(
        default="http://127.0.0.1:3000/auth/callback",
        alias="OIDC_REDIRECT_URI",
    )

    # LLM Advisory Configuration (Optional, keys server-side only)
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_provider: str = Field(default="openai-compatible", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_base_url: Optional[str] = Field(default=None, alias="LLM_BASE_URL")
    llm_timeout_seconds: float = Field(default=15.0, alias="LLM_TIMEOUT_SECONDS")

    # ML Classifier Defaults
    default_confidence_threshold: float = 0.70
    default_margin_threshold: float = 0.20
    model_storage_path: str = "./data/models"

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if v_clean not in {"development", "testing", "production", "staging"}:
            return "development"
        return v_clean

    def check_production_guard(self) -> None:
        """Enforces that demo mode is strictly refused in production."""
        if self.environment == "production" and self.demo_mode:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Demo mode cannot be enabled in production environment."
            )


settings = Settings()
settings.check_production_guard()
