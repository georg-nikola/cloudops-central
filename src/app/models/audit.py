"""
CloudOps Central Audit Models

This module contains database models for audit logging and event tracking,
providing comprehensive activity monitoring and compliance support.
"""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AuditEventType(str, Enum):
    """Enumeration of audit event types."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    POLICY_VIOLATION = "policy_violation"
    INFRASTRUCTURE_DEPLOY = "infrastructure_deploy"
    INFRASTRUCTURE_DESTROY = "infrastructure_destroy"
    COST_ALERT = "cost_alert"
    SECURITY_EVENT = "security_event"


class AuditSeverity(str, Enum):
    """Enumeration of audit event severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditStatus(str, Enum):
    """Enumeration of audit event statuses."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class AuditLog(BaseModel):
    """
    Model representing audit log entries.

    This captures all significant events and actions within the system
    for security, compliance, and troubleshooting purposes.
    """

    __tablename__ = "audit_logs"

    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType), nullable=False, doc="Type of event being audited"
    )

    severity: Mapped[AuditSeverity] = mapped_column(
        Enum(AuditSeverity),
        nullable=False,
        default=AuditSeverity.INFO,
        doc="Severity level of the event",
    )

    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus),
        nullable=False,
        default=AuditStatus.SUCCESS,
        doc="Status of the audited action",
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        doc="ID of the user who performed the action",
    )

    session_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Session ID when the action was performed"
    )

    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Type of resource affected"
    )

    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, doc="ID of the resource affected"
    )

    resource_identifier: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="Human-readable identifier of the resource"
    )

    action: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="Specific action performed"
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Human-readable description of the event"
    )

    event_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, doc="Additional event data and context"
    )

    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, doc="State of the resource before the action"
    )

    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, doc="State of the resource after the action"
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        INET, nullable=True, doc="IP address from which the action was performed"
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="User agent string of the client"
    )

    api_endpoint: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, doc="API endpoint that was called"
    )

    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Unique request ID for correlation"
    )

    correlation_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Correlation ID for related events"
    )

    duration_ms: Mapped[Optional[int]] = mapped_column(
        nullable=True, doc="Duration of the action in milliseconds"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Error message if the action failed"
    )

    error_code: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="Error code if the action failed"
    )

    tags: Mapped[Dict[str, str]] = mapped_column(
        JSON, nullable=False, default=dict, doc="Tags for categorization and filtering"
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    def add_tag(self, key: str, value: str) -> None:
        """Add a tag to the audit log entry."""
        if self.tags is None:
            self.tags = {}
        self.tags[key] = value

    def get_tag(self, key: str, default: str = None) -> Optional[str]:
        """Get a tag value."""
        if self.tags is None:
            return default
        return self.tags.get(key, default)

    @property
    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        security_events = {
            AuditEventType.LOGIN,
            AuditEventType.LOGOUT,
            AuditEventType.PERMISSION_GRANTED,
            AuditEventType.PERMISSION_REVOKED,
            AuditEventType.SECURITY_EVENT,
        }
        return self.event_type in security_events

    @property
    def is_infrastructure_event(self) -> bool:
        """Check if this is an infrastructure-related event."""
        infrastructure_events = {
            AuditEventType.INFRASTRUCTURE_DEPLOY,
            AuditEventType.INFRASTRUCTURE_DESTROY,
        }
        return self.event_type in infrastructure_events


class AuditEvent(BaseModel):
    """
    Model representing high-level audit events.

    This provides a summary view of related audit log entries
    for easier analysis and reporting.
    """

    __tablename__ = "audit_events"

    event_name: Mapped[str] = mapped_column(
        String(200), nullable=False, doc="Name of the event"
    )

    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType), nullable=False, doc="Type of event"
    )

    severity: Mapped[AuditSeverity] = mapped_column(
        Enum(AuditSeverity),
        nullable=False,
        default=AuditSeverity.INFO,
        doc="Severity level of the event",
    )

    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus),
        nullable=False,
        default=AuditStatus.SUCCESS,
        doc="Overall status of the event",
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        doc="ID of the user who initiated the event",
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Description of the event"
    )

    event_summary: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, doc="Summary of the event and its impact"
    )

    resources_affected: Mapped[int] = mapped_column(
        nullable=False, default=0, doc="Number of resources affected by this event"
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When the event started",
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="When the event completed"
    )

    duration_seconds: Mapped[Optional[int]] = mapped_column(
        nullable=True, doc="Duration of the event in seconds"
    )

    correlation_id: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="Correlation ID linking related audit logs"
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    @property
    def is_completed(self) -> bool:
        """Check if the event has completed."""
        return self.completed_at is not None

    @property
    def is_in_progress(self) -> bool:
        """Check if the event is still in progress."""
        return self.completed_at is None

    def complete(self, status: AuditStatus = AuditStatus.SUCCESS) -> None:
        """Mark the event as completed."""
        self.completed_at = datetime.utcnow()
        self.status = status
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())


class AuditRetentionPolicy(BaseModel):
    """
    Model representing audit log retention policies.

    This defines how long different types of audit logs should be retained.
    """

    __tablename__ = "audit_retention_policies"

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, doc="Name of the retention policy"
    )

    event_types: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="List of event types this policy applies to",
    )

    retention_days: Mapped[int] = mapped_column(
        nullable=False, doc="Number of days to retain audit logs"
    )

    archive_after_days: Mapped[Optional[int]] = mapped_column(
        nullable=True, doc="Number of days after which to archive logs"
    )

    compression_enabled: Mapped[bool] = mapped_column(
        nullable=False, default=True, doc="Whether to compress archived logs"
    )

    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, doc="Whether this policy is active"
    )

    last_cleanup_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Last time cleanup was performed"
    )

    def should_retain(self, log_age_days: int) -> bool:
        """Check if a log should be retained based on its age."""
        return log_age_days <= self.retention_days

    def should_archive(self, log_age_days: int) -> bool:
        """Check if a log should be archived based on its age."""
        if self.archive_after_days is None:
            return False
        return log_age_days >= self.archive_after_days
