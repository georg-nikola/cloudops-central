"""
CloudOps Central Base Models

This module contains base model classes and common mixins used throughout
the application for consistent database schema patterns.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Create the declarative base
Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated",
    )


class UUIDMixin:
    """Mixin for adding UUID primary key to models."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        doc="Unique identifier for the record",
    )


class SoftDeleteMixin:
    """Mixin for adding soft delete functionality to models."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft deleted",
    )

    def soft_delete(self) -> None:
        """Mark the record as soft deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted."""
        return self.deleted_at is not None


class MetadataMixin:
    """Mixin for adding metadata fields to models."""

    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=dict, doc="Additional metadata stored as JSON"
    )

    tags: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON, nullable=True, default=dict, doc="Tags for categorization and filtering"
    )

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata key-value pair."""
        if self.metadata_ is None:
            self.metadata_ = {}
        self.metadata_[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key."""
        if self.metadata_ is None:
            return default
        return self.metadata_.get(key, default)

    def remove_metadata(self, key: str) -> None:
        """Remove metadata key."""
        if self.metadata_ and key in self.metadata_:
            del self.metadata_[key]

    def add_tag(self, key: str, value: str) -> None:
        """Add a tag."""
        if self.tags is None:
            self.tags = {}
        self.tags[key] = value

    def get_tag(self, key: str, default: str = None) -> Optional[str]:
        """Get tag value by key."""
        if self.tags is None:
            return default
        return self.tags.get(key, default)

    def remove_tag(self, key: str) -> None:
        """Remove a tag."""
        if self.tags and key in self.tags:
            del self.tags[key]

    def has_tag(self, key: str, value: str = None) -> bool:
        """Check if tag exists, optionally with specific value."""
        if self.tags is None:
            return False
        if key not in self.tags:
            return False
        if value is not None:
            return self.tags[key] == value
        return True


class AuditMixin:
    """Mixin for adding audit fields to models."""

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, doc="ID of the user who created the record"
    )

    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the user who last updated the record",
    )

    version: Mapped[int] = mapped_column(
        default=1, nullable=False, doc="Version number for optimistic locking"
    )


class NameDescriptionMixin:
    """Mixin for adding name and description fields to models."""

    name: Mapped[str] = mapped_column(String(255), nullable=False, doc="Human-readable name")

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Detailed description"
    )


class StatusMixin:
    """Mixin for adding status tracking to models."""

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", doc="Current status of the record"
    )

    status_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Additional status information"
    )

    def set_status(self, status: str, message: str = None) -> None:
        """Set the status and optional message."""
        self.status = status
        self.status_message = message


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, MetadataMixin, AuditMixin):
    """
    Base model class that includes common functionality.

    This class combines all the useful mixins and serves as the base
    for most models in the application.
    """

    __abstract__ = True

    def to_dict(self, exclude_fields: Optional[set] = None) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.

        Args:
            exclude_fields: Set of field names to exclude from the result

        Returns:
            Dictionary representation of the model
        """
        exclude_fields = exclude_fields or set()
        result = {}

        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                # Handle datetime serialization
                if isinstance(value, datetime):
                    value = value.isoformat()
                # Handle UUID serialization
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                result[column.name] = value

        return result

    def update_from_dict(self, data: Dict[str, Any], exclude_fields: Optional[set] = None) -> None:
        """
        Update model instance from dictionary.

        Args:
            data: Dictionary containing field values
            exclude_fields: Set of field names to exclude from update
        """
        exclude_fields = exclude_fields or {"id", "created_at", "updated_at"}

        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of the model."""
        class_name = self.__class__.__name__
        if hasattr(self, "name"):
            return f"<{class_name}(id={self.id}, name='{self.name}')>"
        return f"<{class_name}(id={self.id})>"


class NamedModel(BaseModel, NameDescriptionMixin, StatusMixin):
    """
    Base model for entities that have names, descriptions, and status.

    This is useful for most business entities in the application.
    """

    __abstract__ = True
