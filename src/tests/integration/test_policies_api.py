"""
Integration tests for policy management API endpoints.
"""

import pytest
from fastapi import status


class TestPolicyEndpoints:
    """Test policy management API endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_policies(self, async_client, db_session):
        """Test GET /api/v1/policies endpoint."""
        response = await async_client.get("/api/v1/policies")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_policy(self, async_client, db_session):
        """Test GET /api/v1/policies/{policy_id} endpoint."""
        policy_id = "policy-123"
        response = await async_client.get(f"/api/v1/policies/{policy_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "name" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_policy(self, async_client, db_session):
        """Test POST /api/v1/policies endpoint."""
        policy_data = {
            "name": "Test Policy",
            "description": "A test policy for integration testing",
            "policy_type": "security",
            "severity": "high",
            "policy_code": "package test\n\ndefault allow = false",
            "rule_engine": "opa",
            "target_resources": ["ec2_instance", "rds_instance"],
        }
        response = await async_client.post("/api/v1/policies", json=policy_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == policy_data["name"]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_update_policy(self, async_client, db_session):
        """Test PUT /api/v1/policies/{policy_id} endpoint."""
        policy_id = "policy-123"
        update_data = {"name": "Updated Policy Name", "severity": "critical"}
        response = await async_client.put(f"/api/v1/policies/{policy_id}", json=update_data)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_delete_policy(self, async_client, db_session):
        """Test DELETE /api/v1/policies/{policy_id} endpoint."""
        policy_id = "policy-123"
        response = await async_client.delete(f"/api/v1/policies/{policy_id}")

        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_check_compliance(self, async_client, db_session):
        """Test POST /api/v1/policies/check-compliance endpoint."""
        check_data = {"resource_id": "i-1234567890abcdef0"}
        response = await async_client.post("/api/v1/policies/check-compliance", json=check_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "compliant" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_list_violations(self, async_client, db_session):
        """Test GET /api/v1/policies/violations endpoint."""
        response = await async_client.get("/api/v1/policies/violations")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestPolicyValidation:
    """Test validation in policy endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_policy_missing_fields(self, async_client, db_session):
        """Test creating policy with missing required fields."""
        invalid_data = {
            "name": "Incomplete Policy"
            # Missing required fields: policy_type, policy_code, etc.
        }
        response = await async_client.post("/api/v1/policies", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_policy_invalid_severity(self, async_client, db_session):
        """Test creating policy with invalid severity."""
        invalid_data = {
            "name": "Test Policy",
            "policy_type": "security",
            "severity": "invalid-severity",
            "rules": {},
        }
        response = await async_client.post("/api/v1/policies", json=invalid_data)

        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]
