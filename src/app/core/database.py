"""
CloudOps Central Database Configuration

This module handles database connection, session management, and provides
utilities for database operations using SQLAlchemy with async support.
"""

import asyncio
from typing import AsyncGenerator, Optional

from sqlalchemy import event, pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create the async engine
engine = create_async_engine(
    settings.get_database_url().replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hour
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create the declarative base
Base = declarative_base()


class DatabaseManager:
    """Database manager for handling connections and sessions."""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.
        
        Yields:
            AsyncSession: Database session
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close the database engine."""
        await self.engine.dispose()
    
    async def health_check(self) -> bool:
        """
        Check database connectivity.
        
        Returns:
            bool: True if database is accessible, False otherwise
        """
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session in FastAPI endpoints.
    
    Yields:
        AsyncSession: Database session
    """
    async for session in db_manager.get_session():
        yield session


class DatabaseTransaction:
    """Context manager for database transactions."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self) -> AsyncSession:
        """Enter the transaction context."""
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the transaction context."""
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            await self.session.commit()


def transaction(session: AsyncSession) -> DatabaseTransaction:
    """
    Create a database transaction context manager.
    
    Args:
        session: Database session
        
    Returns:
        DatabaseTransaction: Transaction context manager
    """
    return DatabaseTransaction(session)


class Repository:
    """Base repository class for database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()
    
    async def refresh(self, instance) -> None:
        """Refresh an instance from the database."""
        await self.session.refresh(instance)
    
    async def execute_raw(self, query: str, params: Optional[dict] = None):
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        result = await self.session.execute(query, params or {})
        return result


# Event listeners for connection management
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database-specific connection parameters."""
    if "postgresql" in settings.get_database_url():
        # PostgreSQL specific settings
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone TO 'UTC'")
            cursor.execute("SET statement_timeout = '30s'")


@event.listens_for(engine.sync_engine, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """Ensure connections are alive when checked out from the pool."""
    connection_record.info['pid'] = dbapi_connection.get_backend_pid()


async def init_db() -> None:
    """Initialize the database, creating all tables."""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def drop_db() -> None:
    """Drop all database tables (use with caution!)."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


async def reset_db() -> None:
    """Reset the database by dropping and recreating all tables."""
    logger.warning("Resetting database - all data will be lost!")
    await drop_db()
    await init_db()
    logger.info("Database reset completed")


# Connection pool monitoring
class ConnectionPoolMonitor:
    """Monitor database connection pool metrics."""
    
    @staticmethod
    def get_pool_status() -> dict:
        """Get current connection pool status."""
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    
    @staticmethod
    async def log_pool_status() -> None:
        """Log current pool status."""
        status = ConnectionPoolMonitor.get_pool_status()
        logger.info(f"Connection pool status: {status}")


# Health check utilities
async def database_health_check() -> dict:
    """
    Comprehensive database health check.
    
    Returns:
        dict: Health check results
    """
    try:
        # Basic connectivity test
        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT version()")
            version = result.scalar()
        
        # Pool status
        pool_status = ConnectionPoolMonitor.get_pool_status()
        
        return {
            "status": "healthy",
            "database_version": version,
            "pool_status": pool_status,
            "engine_url": str(engine.url).replace(engine.url.password or "", "****"),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_status": ConnectionPoolMonitor.get_pool_status(),
        }