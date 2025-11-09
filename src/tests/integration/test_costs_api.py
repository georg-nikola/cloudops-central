"""
Integration tests for cost management API endpoints.
"""

import pytest
from fastapi import status


class TestCostEndpoints:
    """Test cost management API endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_current_costs(self, async_client, db_session):
        """Test GET /api/v1/costs/current endpoint."""
        response = await async_client.get("/api/v1/costs/current")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_cost" in data
        assert "currency" in data
        assert "by_service" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_cost_breakdown(self, async_client, db_session):
        """Test GET /api/v1/costs/breakdown endpoint."""
        response = await async_client.get(
            "/api/v1/costs/breakdown",
            params={
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
                "group_by": "service",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_cost" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_detect_anomalies(self, async_client, db_session):
        """Test GET /api/v1/costs/anomalies endpoint."""
        response = await async_client.get("/api/v1/costs/anomalies")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_forecast(self, async_client, db_session):
        """Test GET /api/v1/costs/forecast endpoint."""
        response = await async_client.get("/api/v1/costs/forecast", params={"days": 30})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "forecasted_cost" in data
        assert "confidence" in data

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_recommendations(self, async_client, db_session):
        """Test GET /api/v1/costs/recommendations endpoint."""
        response = await async_client.get("/api/v1/costs/recommendations")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_cost_trends(self, async_client, db_session):
        """Test GET /api/v1/costs/trends endpoint."""
        response = await async_client.get("/api/v1/costs/trends", params={"period": "30d"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "trend" in data


class TestCostValidation:
    """Test validation in cost endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_invalid_date_range(self, async_client, db_session):
        """Test handling of invalid date range."""
        response = await async_client.get(
            "/api/v1/costs/breakdown",
            params={"start_date": "invalid-date", "end_date": "2025-11-30"},
        )

        # Should return validation error
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_forecast_invalid_days(self, async_client, db_session):
        """Test forecast with invalid days parameter."""
        response = await async_client.get("/api/v1/costs/forecast", params={"days": -1})

        # Should handle gracefully or return validation error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST,
        ]
