"""
Main API router for CloudOps Central.
Aggregates all API v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1 import costs, infrastructure, policies, users

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(
    infrastructure.router, prefix="/infrastructure", tags=["infrastructure"]
)

api_router.include_router(costs.router, prefix="/costs", tags=["costs"])

api_router.include_router(policies.router, prefix="/policies", tags=["policies"])

api_router.include_router(users.router, prefix="/users", tags=["users"])
