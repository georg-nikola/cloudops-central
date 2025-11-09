"""
CloudOps Central User and Authentication Models

This module contains database models for user management, authentication,
and role-based access control (RBAC).
"""

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, NamedModel


class UserStatus(str, enum.Enum):
    """Enumeration of user account statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


class RoleType(str, enum.Enum):
    """Enumeration of role types."""

    SYSTEM = "system"
    ORGANIZATION = "organization"
    PROJECT = "project"
    CUSTOM = "custom"


class PermissionScope(str, enum.Enum):
    """Enumeration of permission scopes."""

    GLOBAL = "global"
    ORGANIZATION = "organization"
    PROJECT = "project"
    RESOURCE = "resource"


class User(NamedModel):
    """
    Model representing a user in the system.

    This stores user account information, authentication details,
    and profile data.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="User's email address (used for login)",
    )

    username: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
        doc="Optional username for the user",
    )

    first_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="User's first name"
    )

    last_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="User's last name"
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="BCrypt hashed password"
    )

    user_status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING_VERIFICATION,
        doc="Current user account status",
    )

    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether user has superuser privileges",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="Whether user's email is verified"
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, doc="URL to user's avatar image"
    )

    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UTC", doc="User's preferred timezone"
    )

    language: Mapped[str] = mapped_column(
        String(10), nullable=False, default="en", doc="User's preferred language"
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Last login timestamp"
    )

    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, doc="IP address of last login"
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        default=0, nullable=False, doc="Number of consecutive failed login attempts"
    )

    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Account locked until this timestamp",
    )

    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Last password change timestamp"
    )

    email_verification_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Token for email verification"
    )

    email_verification_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Email verification token expiration",
    )

    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Token for password reset"
    )

    password_reset_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Password reset token expiration"
    )

    # Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email

    @property
    def display_name(self) -> str:
        """Get user's display name."""
        return self.username or self.full_name

    def is_account_locked(self) -> bool:
        """Check if user account is locked."""
        if self.user_status == UserStatus.LOCKED:
            return True
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def has_permission(
        self, permission: str, resource_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True

        # Check through user roles
        for user_role in self.user_roles:
            if user_role.role.has_permission(permission, resource_id):
                return True

        return False

    def get_roles(self) -> List["Role"]:
        """Get all roles assigned to the user."""
        return [user_role.role for user_role in self.user_roles]


class Role(NamedModel):
    """
    Model representing a role in the RBAC system.

    Roles define sets of permissions that can be assigned to users.
    """

    __tablename__ = "roles"

    role_type: Mapped[RoleType] = mapped_column(
        Enum(RoleType), nullable=False, default=RoleType.CUSTOM, doc="Type of role"
    )

    permissions: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="List of permissions granted by this role",
    )

    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this is a system-defined role",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, doc="Whether this role is active"
    )

    max_users: Mapped[Optional[int]] = mapped_column(
        nullable=True, doc="Maximum number of users that can have this role"
    )

    # Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    def has_permission(
        self, permission: str, resource_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Check if role has a specific permission."""
        # Simple permission check (can be extended for resource-specific permissions)
        return permission in self.permissions

    def add_permission(self, permission: str) -> None:
        """Add a permission to the role."""
        if permission not in self.permissions:
            self.permissions.append(permission)

    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the role."""
        if permission in self.permissions:
            self.permissions.remove(permission)

    def get_user_count(self) -> int:
        """Get the number of users with this role."""
        return len(self.user_roles)


class UserRole(BaseModel):
    """
    Model representing the association between users and roles.

    This implements many-to-many relationship with additional metadata.
    """

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, doc="ID of the user"
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, doc="ID of the role"
    )

    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        doc="ID of the user who granted this role",
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When the role was granted",
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="When the role assignment expires"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this role assignment is active",
    )

    # Scope for resource-specific permissions
    scope: Mapped[PermissionScope] = mapped_column(
        Enum(PermissionScope),
        nullable=False,
        default=PermissionScope.GLOBAL,
        doc="Scope of the role assignment",
    )

    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the specific resource this role applies to",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="user_roles", foreign_keys=[user_id]
    )

    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    granted_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[granted_by]
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role_id",
            "scope",
            "resource_id",
            name="unique_user_role_scope_resource",
        ),
    )

    def is_expired(self) -> bool:
        """Check if the role assignment has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.utcnow()

    def is_valid(self) -> bool:
        """Check if the role assignment is valid and active."""
        return self.is_active and not self.is_expired()


class ApiKey(BaseModel):
    """
    Model representing API keys for programmatic access.

    This allows users to create API keys for automation and integrations.
    """

    __tablename__ = "api_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        doc="ID of the user who owns this API key",
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Human-readable name for the API key"
    )

    key_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, doc="Hashed API key"
    )

    prefix: Mapped[str] = mapped_column(
        String(10), nullable=False, doc="Visible prefix of the API key"
    )

    permissions: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, default=list, doc="List of permissions for this API key"
    )

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Last time this API key was used"
    )

    last_used_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, doc="IP address where key was last used"
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="When this API key expires"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, doc="Whether this API key is active"
    )

    # Relationships
    user: Mapped["User"] = relationship("User")

    def is_expired(self) -> bool:
        """Check if the API key has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.utcnow()

    def is_valid(self) -> bool:
        """Check if the API key is valid and active."""
        return self.is_active and not self.is_expired()
