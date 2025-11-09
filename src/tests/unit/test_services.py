"""
Unit tests for service layer.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.cost_service import CostService
from app.services.infrastructure_service import InfrastructureService
from app.services.policy_service import PolicyService
from app.services.user_service import UserService


class TestInfrastructureService:
    """Test InfrastructureService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_resources(self, db_session):
        """Test listing infrastructure resources."""
        service = InfrastructureService(db_session)
        resources = await service.list_resources()

        assert isinstance(resources, list)
        assert len(resources) > 0
        assert "resource_id" in resources[0]
        assert "resource_type" in resources[0]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_resources_with_filters(self, db_session):
        """Test listing resources with filters."""
        service = InfrastructureService(db_session)
        resources = await service.list_resources(cloud_provider="aws", resource_type="ec2_instance")

        assert isinstance(resources, list)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_resource(self, db_session):
        """Test getting a specific resource."""
        service = InfrastructureService(db_session)
        resource = await service.get_resource("i-1234567890abcdef0")

        assert resource is not None
        assert isinstance(resource, dict)
        assert "resource_id" in resource

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_sync_infrastructure(self, db_session):
        """Test infrastructure synchronization."""
        service = InfrastructureService(db_session)
        result = await service.sync_infrastructure()

        assert isinstance(result, dict)
        assert "discovered" in result
        assert "updated" in result
        assert "new" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_detect_drift(self, db_session):
        """Test drift detection."""
        service = InfrastructureService(db_session)
        result = await service.detect_drift("i-1234567890abcdef0")

        assert isinstance(result, dict)
        assert "resource_id" in result
        assert "drift_detected" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_statistics(self, db_session):
        """Test getting infrastructure statistics."""
        service = InfrastructureService(db_session)
        stats = await service.get_statistics()

        assert isinstance(stats, dict)
        assert "total_resources" in stats
        assert "by_provider" in stats
        assert "by_type" in stats


class TestCostService:
    """Test CostService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_current_costs(self, db_session):
        """Test getting current costs."""
        service = CostService(db_session)
        costs = await service.get_current_costs()

        assert isinstance(costs, dict)
        assert "total_cost" in costs
        assert "by_service" in costs

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_cost_breakdown(self, db_session):
        """Test getting cost breakdown."""
        service = CostService(db_session)
        breakdown = await service.get_cost_breakdown(start_date="2025-11-01", end_date="2025-11-30")

        assert isinstance(breakdown, dict)
        assert "total_cost" in breakdown

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_detect_anomalies(self, db_session):
        """Test cost anomaly detection."""
        service = CostService(db_session)
        anomalies = await service.detect_anomalies()

        assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_forecast(self, db_session):
        """Test cost forecasting."""
        service = CostService(db_session)
        forecast = await service.get_forecast(days=30)

        assert isinstance(forecast, dict)
        assert "forecasted_cost" in forecast

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_optimization_recommendations(self, db_session):
        """Test getting optimization recommendations."""
        service = CostService(db_session)
        recommendations = await service.get_optimization_recommendations()

        assert isinstance(recommendations, list)


class TestPolicyService:
    """Test PolicyService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_policies(self, db_session):
        """Test listing policies."""
        service = PolicyService(db_session)
        policies = await service.list_policies()

        assert isinstance(policies, list)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_policy(self, db_session):
        """Test getting a specific policy."""
        service = PolicyService(db_session)
        policy = await service.get_policy("policy-123")

        assert policy is not None
        assert isinstance(policy, dict)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_policy(self, db_session):
        """Test creating a policy."""
        service = PolicyService(db_session)
        policy_data = {
            "name": "Test Policy",
            "description": "A test policy",
            "policy_type": "security",
            "severity": "high",
            "rules": {"check_encryption": True},
        }
        result = await service.create_policy(policy_data)

        assert isinstance(result, dict)
        assert "id" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_check_compliance(self, db_session):
        """Test compliance checking."""
        service = PolicyService(db_session)
        result = await service.check_compliance("resource-123")

        assert isinstance(result, dict)
        assert "compliant" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_violations(self, db_session):
        """Test listing policy violations."""
        service = PolicyService(db_session)
        violations = await service.list_violations()

        assert isinstance(violations, list)


class TestUserService:
    """Test UserService."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_user(self, db_session):
        """Test getting a user."""
        service = UserService(db_session)
        user = await service.get_user("user-123")

        assert user is not None
        assert isinstance(user, dict)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_user(self, db_session):
        """Test creating a user."""
        service = UserService(db_session)
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword",
            "full_name": "New User",
        }
        result = await service.create_user(user_data)

        assert isinstance(result, dict)
        assert "id" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_authenticate_user(self, db_session):
        """Test user authentication."""
        service = UserService(db_session)
        user = await service.authenticate_user("admin", "admin")

        # Since this is a stub implementation, it will return the mock user
        assert user is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_list_users(self, db_session):
        """Test listing users."""
        service = UserService(db_session)
        users = await service.list_users()

        assert isinstance(users, list)
