"""
Pytest configuration and fixtures for CloudOps Central tests.

This module provides shared fixtures for all test types including:
- Database setup and teardown
- Redis mocking
- Authentication fixtures
- HTTP client fixtures
- Mock cloud provider clients
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db
from app.models.costs import CostRecord
from app.models.infrastructure import CloudProvider, InfrastructureResource
from app.models.policies import Policy
from app.models.users import Role, User, UserStatus

# Import the app and dependencies
from main import app

# ============================================
# Test Configuration
# ============================================


def get_test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/15",  # Use separate Redis DB for tests
        SECRET_KEY="test-secret-key",
        JWT_SECRET_KEY="test-jwt-secret",
        ENABLE_METRICS=False,
    )


# Override the settings dependency
app.dependency_overrides[get_settings] = get_test_settings


# ============================================
# Database Fixtures
# ============================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def db_session(
    test_db_session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """Override the get_db dependency with test database."""

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db
    yield test_db_session
    app.dependency_overrides.pop(get_db, None)


# ============================================
# HTTP Client Fixtures
# ============================================


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a synchronous test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an asynchronous test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================
# Authentication Fixtures
# ============================================


@pytest.fixture
def test_user_data() -> dict:
    """Test user data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "hashed_password": "hashed_password_placeholder",
        "user_status": UserStatus.ACTIVE,
        "is_superuser": False,
        "is_verified": True,
    }


@pytest.fixture
def test_admin_data() -> dict:
    """Test admin user data."""
    return {
        "email": "admin@example.com",
        "username": "admin",
        "first_name": "Admin",
        "last_name": "User",
        "hashed_password": "hashed_admin_password",
        "user_status": UserStatus.ACTIVE,
        "is_superuser": True,
        "is_verified": True,
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict) -> User:
    """Create a test user in the database."""
    user = User(**test_user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession, test_admin_data: dict) -> User:
    """Create a test admin user in the database."""
    admin = User(**test_admin_data)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_headers(test_user_data: dict) -> dict:
    """Create authentication headers with JWT token."""
    # In a real scenario, generate a proper JWT token
    # For now, we'll use a mock token
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json",
    }


@pytest.fixture
def admin_auth_headers(test_admin_data: dict) -> dict:
    """Create admin authentication headers with JWT token."""
    return {
        "Authorization": "Bearer admin-test-token",
        "Content-Type": "application/json",
    }


# ============================================
# Model Fixtures
# ============================================


@pytest_asyncio.fixture
async def test_cloud_provider(db_session: AsyncSession) -> CloudProvider:
    """Create a test cloud provider."""
    provider = CloudProvider(
        name="AWS",
        provider_type="aws",
        description="Amazon Web Services",
        is_enabled=True,
        configuration={"region": "us-east-1"},
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)
    return provider


@pytest_asyncio.fixture
async def test_resource_type(db_session: AsyncSession) -> "ResourceType":
    """Create a test resource type."""
    from app.models.infrastructure import ResourceType

    resource_type = ResourceType(
        name="EC2 Instance",
        resource_category="compute",
        cloud_provider_type="aws",
        icon="server",
    )
    db_session.add(resource_type)
    await db_session.commit()
    await db_session.refresh(resource_type)
    return resource_type


@pytest_asyncio.fixture
async def test_infrastructure_resource(
    db_session: AsyncSession,
    test_cloud_provider: CloudProvider,
    test_resource_type: "ResourceType",
) -> InfrastructureResource:
    """Create a test infrastructure resource."""
    from app.models.infrastructure import ResourceStatus

    resource = InfrastructureResource(
        name="test-instance",
        description="Test EC2 instance",
        cloud_provider_id=test_cloud_provider.id,
        resource_type_id=test_resource_type.id,
        external_id="i-1234567890abcdef0",
        region="us-east-1",
        resource_status=ResourceStatus.RUNNING,
        configuration={"instance_type": "t3.medium"},
    )
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)
    return resource


@pytest_asyncio.fixture
async def test_policy(db_session: AsyncSession) -> Policy:
    """Create a test policy."""
    from app.models.policies import PolicySeverity, PolicyType, RuleEngine

    policy = Policy(
        name="Test Security Policy",
        description="A test policy for security compliance",
        policy_type=PolicyType.SECURITY,
        severity=PolicySeverity.HIGH,
        policy_code="package cloudops\n\ndefault allow = false",
        rule_engine=RuleEngine.OPA,
        target_resources=["ec2_instance", "rds_instance"],
    )
    db_session.add(policy)
    await db_session.commit()
    await db_session.refresh(policy)
    return policy


@pytest_asyncio.fixture
async def test_cost_record(
    db_session: AsyncSession,
    test_infrastructure_resource: InfrastructureResource,
    test_cloud_provider: CloudProvider,
) -> CostRecord:
    """Create a test cost record."""
    from datetime import datetime, timedelta
    from decimal import Decimal

    now = datetime.utcnow()
    cost = CostRecord(
        resource_id=test_infrastructure_resource.id,
        cloud_provider_id=test_cloud_provider.id,
        service_name="EC2",
        resource_type="Instance",
        resource_identifier="i-1234567890abcdef0",
        region="us-east-1",
        cost_amount=Decimal("125.50"),
        currency="USD",
        billing_period_start=now - timedelta(days=1),
        billing_period_end=now,
        cost_details={},
    )
    db_session.add(cost)
    await db_session.commit()
    await db_session.refresh(cost)
    return cost


# ============================================
# Mock Cloud Provider Fixtures
# ============================================


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client for AWS."""
    mock = MagicMock()
    mock.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-1234567890abcdef0",
                        "InstanceType": "t3.medium",
                        "State": {"Name": "running"},
                    }
                ]
            }
        ]
    }
    return mock


@pytest.fixture
def mock_azure_client():
    """Mock Azure client."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_gcp_client():
    """Mock GCP client."""
    mock = MagicMock()
    return mock


# ============================================
# Redis Fixtures
# ============================================


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    return mock


# ============================================
# Environment Fixtures
# ============================================


@pytest.fixture(scope="function", autouse=True)
def test_env_vars():
    """Set test environment variables."""
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    yield
    # Cleanup
    for key in ["ENVIRONMENT", "DEBUG", "DATABASE_URL"]:
        os.environ.pop(key, None)


# ============================================
# Utility Fixtures
# ============================================


@pytest.fixture
def sample_api_response() -> dict:
    """Sample API response for testing."""
    return {
        "status": "success",
        "data": {"id": 1, "name": "test"},
        "message": "Operation completed successfully",
    }


@pytest.fixture
def sample_error_response() -> dict:
    """Sample error response for testing."""
    return {
        "error": {
            "type": "validation_error",
            "message": "Invalid input data",
            "details": {"field": "value"},
        }
    }


# ============================================
# Cleanup Fixtures
# ============================================


@pytest.fixture(scope="function", autouse=True)
async def cleanup_after_test(db_session: AsyncSession):
    """Cleanup database after each test."""
    yield
    # Rollback any uncommitted changes
    await db_session.rollback()
