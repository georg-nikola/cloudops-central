"""
CloudOps Central Configuration Module

This module contains all configuration settings for the CloudOps Central application.
It uses Pydantic settings for type validation and environment variable management.
"""

import os
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application Information
    APP_NAME: str = Field(default="CloudOps Central", env="APP_NAME")
    APP_VERSION: str = Field(default="0.1.0", env="APP_VERSION")
    APP_DESCRIPTION: str = Field(
        default="Enterprise Infrastructure Management Platform", env="APP_DESCRIPTION"
    )
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # Server Configuration
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    RELOAD: bool = Field(default=True, env="RELOAD")

    # API Configuration
    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")

    # Security
    SECRET_KEY: str = Field(default="your-super-secret-key", env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret-key", env="JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    BCRYPT_ROUNDS: int = Field(default=12, env="BCRYPT_ROUNDS")
    SESSION_MAX_AGE: int = Field(default=3600, env="SESSION_MAX_AGE")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="BACKEND_CORS_ORIGINS",
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"], env="ALLOWED_HOSTS"
    )

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql://cloudops:cloudops123@localhost:5432/cloudops_central",
        env="DATABASE_URL",
    )
    DATABASE_HOST: str = Field(default="localhost", env="DATABASE_HOST")
    DATABASE_PORT: int = Field(default=5432, env="DATABASE_PORT")
    DATABASE_NAME: str = Field(default="cloudops_central", env="DATABASE_NAME")
    DATABASE_USER: str = Field(default="cloudops", env="DATABASE_USER")
    DATABASE_PASSWORD: str = Field(default="cloudops123", env="DATABASE_PASSWORD")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # Celery Configuration
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1", env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND"
    )
    CELERY_TASK_SERIALIZER: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    CELERY_ACCEPT_CONTENT: List[str] = Field(
        default=["json"], env="CELERY_ACCEPT_CONTENT"
    )
    CELERY_RESULT_SERIALIZER: str = Field(
        default="json", env="CELERY_RESULT_SERIALIZER"
    )
    CELERY_TIMEZONE: str = Field(default="UTC", env="CELERY_TIMEZONE")

    # AWS Configuration
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None, env="AWS_SECRET_ACCESS_KEY"
    )
    AWS_S3_BUCKET: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")

    # Azure Configuration
    AZURE_CLIENT_ID: Optional[str] = Field(default=None, env="AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET: Optional[str] = Field(default=None, env="AZURE_CLIENT_SECRET")
    AZURE_TENANT_ID: Optional[str] = Field(default=None, env="AZURE_TENANT_ID")
    AZURE_SUBSCRIPTION_ID: Optional[str] = Field(
        default=None, env="AZURE_SUBSCRIPTION_ID"
    )

    # GCP Configuration
    GCP_PROJECT_ID: Optional[str] = Field(default=None, env="GCP_PROJECT_ID")
    GCP_CREDENTIALS_PATH: Optional[str] = Field(
        default=None, env="GCP_CREDENTIALS_PATH"
    )

    # External Services
    PROMETHEUS_URL: str = Field(default="http://localhost:9090", env="PROMETHEUS_URL")
    GRAFANA_URL: str = Field(default="http://localhost:3000", env="GRAFANA_URL")
    GRAFANA_API_KEY: Optional[str] = Field(default=None, env="GRAFANA_API_KEY")

    # Email Configuration
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")

    # Feature Flags
    ENABLE_COST_OPTIMIZATION: bool = Field(default=True, env="ENABLE_COST_OPTIMIZATION")
    ENABLE_POLICY_ENGINE: bool = Field(default=True, env="ENABLE_POLICY_ENGINE")
    ENABLE_DRIFT_DETECTION: bool = Field(default=True, env="ENABLE_DRIFT_DETECTION")
    ENABLE_BACKUP_AUTOMATION: bool = Field(default=True, env="ENABLE_BACKUP_AUTOMATION")

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    RATE_LIMIT_BURST: int = Field(default=10, env="RATE_LIMIT_BURST")

    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=8001, env="METRICS_PORT")

    # Development Settings
    DEV_MODE: bool = Field(default=False, env="DEV_MODE")

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse allowed hosts from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("CELERY_ACCEPT_CONTENT", pre=True)
    def assemble_celery_accept_content(
        cls, v: Union[str, List[str]]
    ) -> Union[List[str], str]:
        """Parse Celery accept content from environment variable."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_environments = ["development", "staging", "production", "testing"]
        if v.lower() not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of {valid_environments}")
        return v.lower()

    def get_database_url(self) -> str:
        """Get the complete database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    def get_redis_url(self) -> str:
        """Get the complete Redis URL."""
        if self.REDIS_URL:
            return self.REDIS_URL

        auth_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT == "testing"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function uses lru_cache to ensure settings are loaded only once
    and cached for subsequent calls, improving performance.
    """
    return Settings()


# Global settings instance
settings = get_settings()
