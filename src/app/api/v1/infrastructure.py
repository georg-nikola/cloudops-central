"""
Infrastructure management API endpoints.
Provides CRUD operations for cloud infrastructure resources.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.infrastructure_service import InfrastructureService

router = APIRouter()


class InfrastructureResourceBase(BaseModel):
    """Base schema for infrastructure resources."""

    resource_id: str
    resource_type: str
    cloud_provider: str
    region: str
    name: Optional[str] = None
    tags: Optional[dict] = None
    configuration: Optional[dict] = None


class InfrastructureResourceResponse(InfrastructureResourceBase):
    """Response schema for infrastructure resources."""

    id: int
    status: str
    drift_detected: bool
    last_synced: Optional[str] = None

    class Config:
        from_attributes = True


class DriftDetectionResponse(BaseModel):
    """Response schema for drift detection."""

    resource_id: str
    drift_detected: bool
    drift_details: Optional[dict] = None


@router.get("/resources", response_model=List[InfrastructureResourceResponse])
async def list_resources(
    cloud_provider: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """
    List infrastructure resources with optional filtering.

    - **cloud_provider**: Filter by cloud provider (aws, azure, gcp)
    - **resource_type**: Filter by resource type (ec2, s3, rds, etc.)
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    service = InfrastructureService(db)
    resources = await service.list_resources(
        cloud_provider=cloud_provider,
        resource_type=resource_type,
        skip=skip,
        limit=limit,
    )
    return resources


@router.get("/resources/{resource_id}", response_model=InfrastructureResourceResponse)
async def get_resource(resource_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific infrastructure resource by ID."""
    service = InfrastructureService(db)
    resource = await service.get_resource(resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource {resource_id} not found",
        )
    return resource


@router.post("/sync")
async def sync_infrastructure(
    cloud_provider: Optional[str] = None, db: AsyncSession = Depends(get_db)
):
    """
    Trigger infrastructure synchronization.
    Discovers and updates resource inventory from cloud providers.
    """
    service = InfrastructureService(db)
    result = await service.sync_infrastructure(cloud_provider)
    return {
        "message": "Infrastructure sync initiated",
        "cloud_provider": cloud_provider or "all",
        "resources_discovered": result.get("discovered", 0),
        "resources_updated": result.get("updated", 0),
    }


@router.post("/resources/{resource_id}/detect-drift", response_model=DriftDetectionResponse)
async def detect_drift(resource_id: str, db: AsyncSession = Depends(get_db)):
    """
    Detect configuration drift for a specific resource.
    Compares actual state with expected state from IaC.
    """
    service = InfrastructureService(db)
    drift_result = await service.detect_drift(resource_id)
    return drift_result


@router.get("/statistics")
async def get_statistics(cloud_provider: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Get infrastructure statistics and metrics.
    Provides aggregated data about resources, costs, and compliance.
    """
    service = InfrastructureService(db)
    stats = await service.get_statistics(cloud_provider)
    return stats
