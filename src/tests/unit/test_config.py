"""
Unit tests for configuration module.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


class TestSettings:
    """Test Settings configuration class."""

    @pytest.mark.unit
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()

        assert settings.APP_NAME == "CloudOps Central"
        assert settings.APP_VERSION == "1.0.0"
        assert settings.DEBUG is True
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000

    @pytest.mark.unit
    def test_database_url_construction(self):
        """Test database URL construction."""
        settings = Settings(
            DATABASE_HOST="testhost",
            DATABASE_PORT=5433,
            DATABASE_NAME="testdb",
            DATABASE_USER="testuser",
            DATABASE_PASSWORD="testpass",
        )

        db_url = settings.get_database_url()
        assert "testhost" in db_url
        assert "5433" in db_url
        assert "testdb" in db_url
        assert "testuser" in db_url
        assert "testpass" in db_url

    @pytest.mark.unit
    def test_redis_url_construction(self):
        """Test Redis URL construction."""
        settings = Settings(
            REDIS_HOST="redishost",
            REDIS_PORT=6380,
            REDIS_DB=1,
        )

        redis_url = settings.get_redis_url()
        assert "redishost" in redis_url
        assert "6380" in redis_url
        assert "/1" in redis_url

    @pytest.mark.unit
    def test_environment_validation(self):
        """Test environment validation."""
        # Valid environments
        for env in ["development", "staging", "production", "testing"]:
            settings = Settings(ENVIRONMENT=env)
            assert settings.ENVIRONMENT == env.lower()

        # Invalid environment should raise validation error
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="invalid")

    @pytest.mark.unit
    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(LOG_LEVEL=level)
            assert settings.LOG_LEVEL == level.upper()

        # Invalid log level should raise validation error
        with pytest.raises(ValidationError):
            Settings(LOG_LEVEL="INVALID")

    @pytest.mark.unit
    def test_is_production(self):
        """Test is_production method."""
        settings_prod = Settings(ENVIRONMENT="production")
        settings_dev = Settings(ENVIRONMENT="development")

        assert settings_prod.is_production() is True
        assert settings_dev.is_production() is False

    @pytest.mark.unit
    def test_is_development(self):
        """Test is_development method."""
        settings_dev = Settings(ENVIRONMENT="development")
        settings_prod = Settings(ENVIRONMENT="production")

        assert settings_dev.is_development() is True
        assert settings_prod.is_development() is False

    @pytest.mark.unit
    def test_is_testing(self):
        """Test is_testing method."""
        settings_test = Settings(ENVIRONMENT="testing")
        settings_prod = Settings(ENVIRONMENT="production")

        assert settings_test.is_testing() is True
        assert settings_prod.is_testing() is False

    @pytest.mark.unit
    def test_cors_origins_parsing(self):
        """Test CORS origins parsing from string."""
        settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:3001")

        assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
        assert len(settings.BACKEND_CORS_ORIGINS) == 2
        assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS

    @pytest.mark.unit
    def test_feature_flags(self):
        """Test feature flags."""
        settings = Settings(
            ENABLE_COST_OPTIMIZATION=True,
            ENABLE_POLICY_ENGINE=False,
            ENABLE_DRIFT_DETECTION=True,
        )

        assert settings.ENABLE_COST_OPTIMIZATION is True
        assert settings.ENABLE_POLICY_ENGINE is False
        assert settings.ENABLE_DRIFT_DETECTION is True


class TestGetSettings:
    """Test get_settings function."""

    @pytest.mark.unit
    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should return the same instance due to lru_cache
        assert settings1 is settings2
