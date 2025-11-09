"""
Unit tests for database models.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.base import BaseModel, NamedModel
from app.models.costs import CostRecord
from app.models.infrastructure import CloudProvider, InfrastructureResource
from app.models.policies import Policy
from app.models.users import Role, User


class TestBaseModelMixins:
    """Test base model mixins functionality."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_uuid_mixin(self, db_session):
        """Test UUID primary key generation."""
        provider = CloudProvider(
            name="Test Provider",
            provider_type="aws",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.commit()

        assert isinstance(provider.id, uuid.UUID)
        assert provider.id is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_timestamp_mixin(self, db_session):
        """Test automatic timestamp generation."""
        provider = CloudProvider(
            name="Test Provider",
            provider_type="aws",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.commit()

        assert isinstance(provider.created_at, datetime)
        assert isinstance(provider.updated_at, datetime)
        assert provider.created_at <= provider.updated_at

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_soft_delete_mixin(self, db_session):
        """Test soft delete functionality."""
        provider = CloudProvider(
            name="Test Provider",
            provider_type="aws",
            is_enabled=True,
        )
        db_session.add(provider)
        await db_session.commit()

        # Test soft delete
        assert not provider.is_deleted
        provider.soft_delete()
        assert provider.is_deleted
        assert provider.deleted_at is not None

        # Test restore
        provider.restore()
        assert not provider.is_deleted
        assert provider.deleted_at is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_metadata_mixin(self, db_session):
        """Test metadata and tags functionality."""
        provider = CloudProvider(
            name="Test Provider",
            provider_type="aws",
            is_enabled=True,
        )

        # Test metadata
        provider.add_metadata("key1", "value1")
        assert provider.get_metadata("key1") == "value1"
        assert provider.get_metadata("nonexistent", "default") == "default"

        provider.remove_metadata("key1")
        assert provider.get_metadata("key1") is None

        # Test tags
        provider.add_tag("environment", "production")
        assert provider.get_tag("environment") == "production"
        assert provider.has_tag("environment")
        assert provider.has_tag("environment", "production")
        assert not provider.has_tag("environment", "staging")

        provider.remove_tag("environment")
        assert not provider.has_tag("environment")


class TestCloudProviderModel:
    """Test CloudProvider model."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_cloud_provider(self, db_session):
        """Test creating a cloud provider."""
        provider = CloudProvider(
            name="AWS",
            provider_type="aws",
            description="Amazon Web Services",
            is_enabled=True,
            configuration={"region": "us-east-1"},
        )
        db_session.add(provider)
        await db_session.commit()

        result = await db_session.execute(
            select(CloudProvider).where(CloudProvider.name == "AWS")
        )
        saved_provider = result.scalar_one()

        assert saved_provider.name == "AWS"
        assert saved_provider.provider_type == "aws"
        assert saved_provider.is_enabled is True
        assert saved_provider.configuration["region"] == "us-east-1"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_cloud_provider_to_dict(self, test_cloud_provider):
        """Test converting cloud provider to dictionary."""
        provider_dict = test_cloud_provider.to_dict()

        assert isinstance(provider_dict, dict)
        assert "id" in provider_dict
        assert "name" in provider_dict
        assert provider_dict["name"] == "AWS"


class TestInfrastructureResourceModel:
    """Test InfrastructureResource model."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_infrastructure_resource(
        self, db_session, test_cloud_provider, test_resource_type
    ):
        """Test creating an infrastructure resource."""
        from app.models.infrastructure import ResourceStatus

        resource = InfrastructureResource(
            name="web-server",
            description="Web server instance",
            external_id="i-1234567890",
            cloud_provider_id=test_cloud_provider.id,
            resource_type_id=test_resource_type.id,
            region="us-east-1",
            resource_status=ResourceStatus.RUNNING,
            configuration={"instance_type": "t3.medium"},
        )
        db_session.add(resource)
        await db_session.commit()

        result = await db_session.execute(
            select(InfrastructureResource).where(
                InfrastructureResource.external_id == "i-1234567890"
            )
        )
        saved_resource = result.scalar_one()

        assert saved_resource.name == "web-server"
        assert saved_resource.resource_status == ResourceStatus.RUNNING
        assert saved_resource.cloud_provider_id == test_cloud_provider.id


class TestUserModel:
    """Test User model."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_user(self, db_session):
        """Test creating a user."""
        from app.models.users import UserStatus

        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            hashed_password="hashed_password_here",
            user_status=UserStatus.ACTIVE,
        )
        db_session.add(user)
        await db_session.commit()

        result = await db_session.execute(
            select(User).where(User.email == "test@example.com")
        )
        saved_user = result.scalar_one()

        assert saved_user.username == "testuser"
        assert saved_user.first_name == "Test"
        assert saved_user.last_name == "User"
        assert saved_user.user_status == UserStatus.ACTIVE


class TestPolicyModel:
    """Test Policy model."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_policy(self, db_session):
        """Test creating a policy."""
        from app.models.policies import PolicySeverity, PolicyType, RuleEngine

        policy = Policy(
            name="Security Policy",
            description="Test security policy",
            policy_type=PolicyType.SECURITY,
            severity=PolicySeverity.HIGH,
            policy_code="package test\n\ndefault allow = false",
            rule_engine=RuleEngine.OPA,
            target_resources=["ec2_instance"],
        )
        db_session.add(policy)
        await db_session.commit()

        result = await db_session.execute(
            select(Policy).where(Policy.name == "Security Policy")
        )
        saved_policy = result.scalar_one()

        assert saved_policy.policy_type == PolicyType.SECURITY
        assert saved_policy.severity == PolicySeverity.HIGH
        assert "package test" in saved_policy.policy_code


class TestCostRecordModel:
    """Test CostRecord model."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_cost_record(
        self, db_session, test_infrastructure_resource, test_cloud_provider
    ):
        """Test creating a cost record."""
        from datetime import datetime, timedelta
        from decimal import Decimal

        now = datetime.utcnow()
        cost = CostRecord(
            resource_id=test_infrastructure_resource.id,
            cloud_provider_id=test_cloud_provider.id,
            service_name="EC2",
            resource_type="Instance",
            resource_identifier="i-test-123",
            region="us-east-1",
            cost_amount=Decimal("150.75"),
            currency="USD",
            billing_period_start=now - timedelta(days=1),
            billing_period_end=now,
            cost_details={},
        )
        db_session.add(cost)
        await db_session.commit()

        result = await db_session.execute(
            select(CostRecord).where(
                CostRecord.resource_id == test_infrastructure_resource.id
            )
        )
        saved_cost = result.scalar_one()

        assert saved_cost.cost_amount == Decimal("150.75")
        assert saved_cost.currency == "USD"
        assert saved_cost.service_name == "EC2"
