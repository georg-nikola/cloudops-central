"""
User management API endpoints.
Provides user authentication and authorization.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.services.user_service import UserService

router = APIRouter()


class UserBase(BaseModel):
    """Base schema for users."""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str


class UserResponse(UserBase):
    """Response schema for users."""
    id: int
    role: str
    created_at: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


@router.get("/", response_model=List[UserResponse])
async def list_users(
    is_active: Optional[bool] = Query(None),
    role: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users with optional filtering.

    - **is_active**: Filter by active status
    - **role**: Filter by user role
    """
    service = UserService(db)
    users = await service.list_users(
        is_active=is_active,
        role=role,
        skip=skip,
        limit=limit
    )
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user by ID."""
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user."""
    service = UserService(db)

    # Check if username or email already exists
    existing_user = await service.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_email = await service.get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    created_user = await service.create_user(user)
    return created_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing user."""
    service = UserService(db)
    updated_user = await service.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a user."""
    service = UserService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )


@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user permissions and access control information."""
    service = UserService(db)
    permissions = await service.get_user_permissions(user_id)
    if not permissions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return permissions
