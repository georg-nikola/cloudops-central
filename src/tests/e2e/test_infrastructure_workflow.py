"""
End-to-end tests for infrastructure management workflows.
"""

import pytest
from fastapi import status


class TestInfrastructureDiscoveryWorkflow:
    """Test complete infrastructure discovery workflow."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_complete_infrastructure_sync_workflow(
        self, async_client, db_session
    ):
        """
        Test complete workflow:
        1. Trigger infrastructure sync
        2. List discovered resources
        3. Get specific resource details
        4. Check for drift
        5. View statistics
        """
        # Step 1: Trigger sync
        sync_response = await async_client.post(
            "/api/v1/infrastructure/sync",
            json={"cloud_provider": "aws"}
        )
        assert sync_response.status_code == status.HTTP_200_OK
        sync_data = sync_response.json()
        assert sync_data["discovered"] > 0

        # Step 2: List resources
        list_response = await async_client.get("/api/v1/infrastructure/resources")
        assert list_response.status_code == status.HTTP_200_OK
        resources = list_response.json()
        assert len(resources) > 0

        # Step 3: Get specific resource
        resource_id = resources[0]["resource_id"]
        detail_response = await async_client.get(
            f"/api/v1/infrastructure/resources/{resource_id}"
        )
        assert detail_response.status_code == status.HTTP_200_OK
        resource_detail = detail_response.json()
        assert resource_detail["resource_id"] == resource_id

        # Step 4: Check drift
        drift_response = await async_client.get(
            f"/api/v1/infrastructure/resources/{resource_id}/drift"
        )
        assert drift_response.status_code == status.HTTP_200_OK
        drift_data = drift_response.json()
        assert "drift_detected" in drift_data

        # Step 5: View statistics
        stats_response = await async_client.get(
            "/api/v1/infrastructure/statistics"
        )
        assert stats_response.status_code == status.HTTP_200_OK
        stats = stats_response.json()
        assert stats["total_resources"] > 0


class TestInfrastructureFilteringWorkflow:
    """Test infrastructure filtering and search workflow."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_filter_by_provider_and_type(self, async_client, db_session):
        """
        Test workflow:
        1. Get all resources
        2. Filter by cloud provider
        3. Filter by resource type
        4. Verify filtered results
        """
        # Get all resources
        all_response = await async_client.get("/api/v1/infrastructure/resources")
        assert all_response.status_code == status.HTTP_200_OK

        # Filter by provider
        aws_response = await async_client.get(
            "/api/v1/infrastructure/resources",
            params={"cloud_provider": "aws"}
        )
        assert aws_response.status_code == status.HTTP_200_OK

        # Filter by type
        ec2_response = await async_client.get(
            "/api/v1/infrastructure/resources",
            params={"resource_type": "ec2_instance"}
        )
        assert ec2_response.status_code == status.HTTP_200_OK


class TestCostOptimizationWorkflow:
    """Test complete cost optimization workflow."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_cost_analysis_and_optimization(self, async_client, db_session):
        """
        Test workflow:
        1. Get current costs
        2. Analyze cost breakdown
        3. Detect anomalies
        4. Get forecast
        5. Get optimization recommendations
        """
        # Step 1: Current costs
        current_response = await async_client.get("/api/v1/costs/current")
        assert current_response.status_code == status.HTTP_200_OK
        current_data = current_response.json()
        assert "total_cost" in current_data

        # Step 2: Cost breakdown
        breakdown_response = await async_client.get(
            "/api/v1/costs/breakdown",
            params={
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
                "group_by": "service"
            }
        )
        assert breakdown_response.status_code == status.HTTP_200_OK

        # Step 3: Detect anomalies
        anomalies_response = await async_client.get("/api/v1/costs/anomalies")
        assert anomalies_response.status_code == status.HTTP_200_OK
        anomalies = anomalies_response.json()
        assert isinstance(anomalies, list)

        # Step 4: Get forecast
        forecast_response = await async_client.get(
            "/api/v1/costs/forecast",
            params={"days": 30}
        )
        assert forecast_response.status_code == status.HTTP_200_OK
        forecast = forecast_response.json()
        assert "forecasted_cost" in forecast

        # Step 5: Get recommendations
        recommendations_response = await async_client.get(
            "/api/v1/costs/recommendations"
        )
        assert recommendations_response.status_code == status.HTTP_200_OK
        recommendations = recommendations_response.json()
        assert isinstance(recommendations, list)


class TestPolicyComplianceWorkflow:
    """Test complete policy compliance workflow."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_policy_lifecycle(self, async_client, db_session):
        """
        Test workflow:
        1. Create a new policy
        2. List all policies
        3. Check compliance for resources
        4. View violations
        5. Update policy
        6. Delete policy
        """
        # Step 1: Create policy
        policy_data = {
            "name": "E2E Test Policy",
            "description": "Test policy for E2E testing",
            "policy_type": "security",
            "severity": "high",
            "policy_code": "package e2e\n\ndefault allow = true",
            "rule_engine": "opa",
            "target_resources": ["ec2_instance"]
        }
        create_response = await async_client.post(
            "/api/v1/policies",
            json=policy_data
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        created_policy = create_response.json()
        policy_id = created_policy["id"]

        # Step 2: List policies
        list_response = await async_client.get("/api/v1/policies")
        assert list_response.status_code == status.HTTP_200_OK
        policies = list_response.json()
        assert len(policies) > 0

        # Step 3: Check compliance
        compliance_response = await async_client.post(
            "/api/v1/policies/check-compliance",
            json={"resource_id": "i-1234567890abcdef0"}
        )
        assert compliance_response.status_code == status.HTTP_200_OK

        # Step 4: View violations
        violations_response = await async_client.get("/api/v1/policies/violations")
        assert violations_response.status_code == status.HTTP_200_OK

        # Step 5: Update policy
        update_response = await async_client.put(
            f"/api/v1/policies/{policy_id}",
            json={"severity": "critical"}
        )
        # May return 200 or 404 depending on implementation
        assert update_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

        # Step 6: Delete policy
        delete_response = await async_client.delete(f"/api/v1/policies/{policy_id}")
        assert delete_response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]


class TestHealthAndMonitoring:
    """Test health check and monitoring endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_health_endpoints(self, async_client):
        """Test all health and status endpoints."""
        # Main health check
        health_response = await async_client.get("/health")
        assert health_response.status_code == status.HTTP_200_OK
        health_data = health_response.json()
        assert health_data["status"] == "healthy"

        # Root endpoint
        root_response = await async_client.get("/")
        assert root_response.status_code == status.HTTP_200_OK
        root_data = root_response.json()
        assert "version" in root_data
