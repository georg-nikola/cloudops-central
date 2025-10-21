"""
Policy management API endpoints.
Provides policy-as-code enforcement and compliance management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.services.policy_service import PolicyService

router = APIRouter()


class PolicyBase(BaseModel):
    """Base schema for policies."""
    name: str
    description: Optional[str] = None
    policy_type: str
    severity: str
    rules: dict
    enabled: bool = True


class PolicyResponse(PolicyBase):
    """Response schema for policies."""
    id: int
    violation_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PolicyViolationResponse(BaseModel):
    """Response schema for policy violations."""
    id: int
    policy_id: int
    policy_name: str
    resource_id: str
    severity: str
    description: str
    detected_at: str
    resolved: bool

    class Config:
        from_attributes = True


class PolicyEvaluationRequest(BaseModel):
    """Request schema for policy evaluation."""
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None


@router.get("/", response_model=List[PolicyResponse])
async def list_policies(
    policy_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    enabled: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    List all policies with optional filtering.

    - **policy_type**: Filter by policy type (security, compliance, cost, etc.)
    - **severity**: Filter by severity (critical, high, medium, low)
    - **enabled**: Filter by enabled status
    """
    service = PolicyService(db)
    policies = await service.list_policies(
        policy_type=policy_type,
        severity=severity,
        enabled=enabled,
        skip=skip,
        limit=limit
    )
    return policies


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific policy by ID."""
    service = PolicyService(db)
    policy = await service.get_policy(policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found"
        )
    return policy


@router.post("/", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy: PolicyBase,
    db: AsyncSession = Depends(get_db)
):
    """Create a new policy."""
    service = PolicyService(db)
    created_policy = await service.create_policy(policy)
    return created_policy


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: int,
    policy: PolicyBase,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing policy."""
    service = PolicyService(db)
    updated_policy = await service.update_policy(policy_id, policy)
    if not updated_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found"
        )
    return updated_policy


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a policy."""
    service = PolicyService(db)
    deleted = await service.delete_policy(policy_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy {policy_id} not found"
        )


@router.post("/evaluate")
async def evaluate_policies(
    request: PolicyEvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate policies against infrastructure resources.
    Checks all enabled policies and detects violations.
    """
    service = PolicyService(db)
    results = await service.evaluate_policies(
        resource_id=request.resource_id,
        resource_type=request.resource_type
    )
    return results


@router.get("/violations/", response_model=List[PolicyViolationResponse])
async def list_violations(
    policy_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    List policy violations with optional filtering.

    - **policy_id**: Filter by specific policy
    - **severity**: Filter by severity level
    - **resolved**: Filter by resolution status
    """
    service = PolicyService(db)
    violations = await service.list_violations(
        policy_id=policy_id,
        severity=severity,
        resolved=resolved,
        skip=skip,
        limit=limit
    )
    return violations


@router.post("/violations/{violation_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_violation(
    violation_id: int,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Mark a policy violation as resolved."""
    service = PolicyService(db)
    resolved = await service.resolve_violation(violation_id, resolution_notes)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Violation {violation_id} not found"
        )
    return {"message": "Violation resolved successfully"}
