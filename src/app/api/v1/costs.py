"""
Cost tracking and optimization API endpoints.
Provides cost analytics, forecasting, and optimization recommendations.
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.cost_service import CostService

router = APIRouter()


class CostRecordResponse(BaseModel):
    """Response schema for cost records."""

    id: int
    cloud_provider: str
    service: str
    region: str
    amount: float
    currency: str
    recorded_date: date

    class Config:
        from_attributes = True


class CostSummaryResponse(BaseModel):
    """Response schema for cost summary."""

    total_cost: float
    currency: str
    breakdown_by_provider: dict
    breakdown_by_service: dict
    trend: Optional[str] = None


class OptimizationRecommendation(BaseModel):
    """Optimization recommendation schema."""

    recommendation_id: str
    resource_id: str
    recommendation_type: str
    description: str
    estimated_savings: float
    priority: str
    implementation_effort: str


@router.get("/records", response_model=List[CostRecordResponse])
async def list_cost_records(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    cloud_provider: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """
    List cost records with optional filtering.

    - **start_date**: Filter costs from this date
    - **end_date**: Filter costs up to this date
    - **cloud_provider**: Filter by cloud provider
    - **service**: Filter by cloud service
    """
    service_instance = CostService(db)
    records = await service_instance.list_records(
        start_date=start_date,
        end_date=end_date,
        cloud_provider=cloud_provider,
        service=service,
        skip=skip,
        limit=limit,
    )
    return records


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    cloud_provider: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost summary and breakdown.
    Provides aggregated cost data with provider and service breakdowns.
    """
    service = CostService(db)
    summary = await service.get_summary(
        start_date=start_date, end_date=end_date, cloud_provider=cloud_provider
    )
    return summary


@router.get("/forecast")
async def forecast_costs(
    months: int = Query(3, ge=1, le=12),
    cloud_provider: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Forecast future costs using ML models.
    Predicts costs for the specified number of months ahead.
    """
    service = CostService(db)
    forecast = await service.forecast_costs(
        months=months, cloud_provider=cloud_provider
    )
    return forecast


@router.get("/anomalies")
async def detect_anomalies(
    days: int = Query(30, ge=7, le=90),
    cloud_provider: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Detect cost anomalies using ML.
    Identifies unusual spending patterns in the specified time window.
    """
    service = CostService(db)
    anomalies = await service.detect_anomalies(days=days, cloud_provider=cloud_provider)
    return anomalies


@router.get("/optimizations", response_model=List[OptimizationRecommendation])
async def get_optimization_recommendations(
    priority: Optional[str] = Query(None, regex="^(high|medium|low)$"),
    min_savings: Optional[float] = Query(None, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-driven cost optimization recommendations.

    - **priority**: Filter by priority level (high, medium, low)
    - **min_savings**: Minimum estimated monthly savings
    """
    service = CostService(db)
    recommendations = await service.get_optimization_recommendations(
        priority=priority, min_savings=min_savings
    )
    return recommendations
