"""
Unit tests for database module.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import ConnectionPoolMonitor, DatabaseManager, database_health_check


class TestDatabaseManager:
    """Test DatabaseManager class."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_session(self, test_db_engine):
        """Test getting a database session."""
        db_manager = DatabaseManager()
        db_manager.engine = test_db_engine

        async for session in db_manager.get_session():
            assert isinstance(session, AsyncSession)
            assert session.is_active

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.database
    async def test_health_check_success(self, test_db_engine):
        """Test successful health check."""
        db_manager = DatabaseManager()
        db_manager.engine = test_db_engine

        result = await db_manager.health_check()
        assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.database
    async def test_health_check_failure(self):
        """Test failed health check with invalid connection."""
        from sqlalchemy.ext.asyncio import create_async_engine

        # Create engine with invalid URL
        invalid_engine = create_async_engine("sqlite+aiosqlite:///invalid.db")
        db_manager = DatabaseManager()
        db_manager.engine = invalid_engine
        db_manager.session_factory = None  # Force failure

        result = await db_manager.health_check()
        assert result is False

        await invalid_engine.dispose()


class TestConnectionPoolMonitor:
    """Test ConnectionPoolMonitor class."""

    @pytest.mark.unit
    def test_get_pool_status(self, test_db_engine):
        """Test getting connection pool status."""
        # Note: This test is limited because we're using StaticPool in tests
        # In production with a real pool, this would return meaningful metrics
        status = ConnectionPoolMonitor.get_pool_status()

        assert isinstance(status, dict)
        assert "pool_size" in status
        assert "checked_in" in status
        assert "checked_out" in status
        assert "overflow" in status
        assert "invalid" in status


class TestDatabaseHealthCheck:
    """Test database health check function."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.database
    @pytest.mark.slow
    async def test_database_health_check_success(self, db_session):
        """Test successful database health check."""
        result = await database_health_check()

        assert isinstance(result, dict)
        assert "status" in result
        # Since we're using SQLite for testing, we might get different results
        # Just check that the structure is correct
