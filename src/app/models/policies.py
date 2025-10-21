"""
CloudOps Central Policy Models

This module contains database models for policy management,
including policies, rules, and violations for compliance enforcement.
"""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, enum
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import NamedModel


class PolicyStatus(str, enum.Enum):
    """Enumeration of policy statuses."""
    
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class PolicySeverity(str, enum.Enum):
    """Enumeration of policy severity levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyType(str, enum.Enum):
    """Enumeration of policy types."""
    
    SECURITY = "security"
    COST = "cost"
    COMPLIANCE = "compliance"
    GOVERNANCE = "governance"
    PERFORMANCE = "performance"
    BACKUP = "backup"


class ViolationStatus(str, enum.Enum):
    """Enumeration of violation statuses."""
    
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    FALSE_POSITIVE = "false_positive"


class RuleEngine(str, enum.Enum):
    """Enumeration of rule engines."""
    
    OPA = "opa"  # Open Policy Agent
    CUSTOM = "custom"
    TERRAFORM = "terraform"
    CLOUD_NATIVE = "cloud_native"


class Policy(NamedModel):
    """
    Model representing a policy for infrastructure governance.
    
    Policies define rules and constraints that infrastructure must comply with.
    """
    
    __tablename__ = "policies"
    
    policy_type: Mapped[PolicyType] = mapped_column(
        enum.Enum(PolicyType),
        nullable=False,
        doc="Type/category of the policy"
    )
    
    policy_status: Mapped[PolicyStatus] = mapped_column(
        enum.Enum(PolicyStatus),
        nullable=False,
        default=PolicyStatus.DRAFT,
        doc="Current status of the policy"
    )
    
    severity: Mapped[PolicySeverity] = mapped_column(
        enum.Enum(PolicySeverity),
        nullable=False,
        default=PolicySeverity.MEDIUM,
        doc="Severity level for violations"
    )
    
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        doc="Policy version"
    )
    
    policy_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Policy implementation code (OPA Rego, custom, etc.)"
    )
    
    rule_engine: Mapped[RuleEngine] = mapped_column(
        enum.Enum(RuleEngine),
        nullable=False,
        default=RuleEngine.OPA,
        doc="Rule engine used to evaluate this policy"
    )
    
    target_resources: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="List of resource types this policy applies to"
    )
    
    target_environments: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="List of environments this policy applies to"
    )
    
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Configurable parameters for the policy"
    )
    
    remediation_actions: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Automated remediation actions"
    )
    
    documentation_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="URL to policy documentation"
    )
    
    is_enforced: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether violations should be enforced"
    )
    
    auto_remediate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether to automatically remediate violations"
    )
    
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether to send notifications for violations"
    )
    
    evaluation_frequency: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="How often to evaluate this policy (cron expression)"
    )
    
    last_evaluated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this policy was evaluated"
    )
    
    # Relationships
    rules: Mapped[List["PolicyRule"]] = relationship(
        "PolicyRule",
        back_populates="policy",
        cascade="all, delete-orphan"
    )
    
    violations: Mapped[List["PolicyViolation"]] = relationship(
        "PolicyViolation",
        back_populates="policy",
        cascade="all, delete-orphan"
    )
    
    def get_active_rules(self) -> List["PolicyRule"]:
        """Get all active rules for this policy."""
        return [rule for rule in self.rules if rule.is_active]
    
    def get_violation_count(self, status: Optional[ViolationStatus] = None) -> int:
        """Get count of violations for this policy."""
        if status:
            return len([v for v in self.violations if v.violation_status == status])
        return len(self.violations)


class PolicyRule(NamedModel):
    """
    Model representing individual rules within a policy.
    
    Rules define specific checks and constraints.
    """
    
    __tablename__ = "policy_rules"
    
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id"),
        nullable=False,
        doc="ID of the parent policy"
    )
    
    rule_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Rule implementation code"
    )
    
    rule_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Type of rule (validation, constraint, etc.)"
    )
    
    severity: Mapped[PolicySeverity] = mapped_column(
        enum.Enum(PolicySeverity),
        nullable=False,
        default=PolicySeverity.MEDIUM,
        doc="Severity level for this rule"
    )
    
    parameters: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Rule-specific parameters"
    )
    
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Error message shown when rule fails"
    )
    
    remediation_hint: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Hint for how to remediate violations"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this rule is active"
    )
    
    order_index: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        doc="Order of execution for this rule"
    )
    
    # Relationships
    policy: Mapped["Policy"] = relationship(
        "Policy",
        back_populates="rules"
    )


class PolicyViolation(NamedModel):
    """
    Model representing a policy violation.
    
    This tracks instances where infrastructure doesn't comply with policies.
    """
    
    __tablename__ = "policy_violations"
    
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id"),
        nullable=False,
        doc="ID of the violated policy"
    )
    
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the resource that violated the policy"
    )
    
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Type of resource that violated the policy"
    )
    
    resource_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Identifier of the violating resource"
    )
    
    violation_status: Mapped[ViolationStatus] = mapped_column(
        enum.Enum(ViolationStatus),
        nullable=False,
        default=ViolationStatus.OPEN,
        doc="Current status of the violation"
    )
    
    severity: Mapped[PolicySeverity] = mapped_column(
        enum.Enum(PolicySeverity),
        nullable=False,
        doc="Severity of this violation"
    )
    
    violation_details: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Detailed information about the violation"
    )
    
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When the violation was first detected"
    )
    
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When the violation was last seen"
    )
    
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the violation was resolved"
    )
    
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the user who resolved the violation"
    )
    
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Notes about how the violation was resolved"
    )
    
    suppressed_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Violation is suppressed until this time"
    )
    
    suppression_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for suppressing the violation"
    )
    
    auto_remediation_attempted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether auto-remediation was attempted"
    )
    
    remediation_details: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Details about remediation attempts"
    )
    
    # Relationships
    policy: Mapped["Policy"] = relationship(
        "Policy",
        back_populates="violations"
    )
    
    def is_active(self) -> bool:
        """Check if violation is currently active."""
        return self.violation_status == ViolationStatus.OPEN
    
    def is_suppressed(self) -> bool:
        """Check if violation is currently suppressed."""
        if self.violation_status == ViolationStatus.SUPPRESSED:
            return True
        if self.suppressed_until and self.suppressed_until > datetime.utcnow():
            return True
        return False
    
    def resolve(self, resolved_by: uuid.UUID, notes: str = None) -> None:
        """Mark violation as resolved."""
        self.violation_status = ViolationStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        if notes:
            self.resolution_notes = notes
    
    def suppress(self, reason: str, until: Optional[datetime] = None) -> None:
        """Suppress the violation."""
        self.violation_status = ViolationStatus.SUPPRESSED
        self.suppression_reason = reason
        self.suppressed_until = until
    
    def acknowledge(self) -> None:
        """Acknowledge the violation."""
        self.violation_status = ViolationStatus.ACKNOWLEDGED


class PolicyExemption(NamedModel):
    """
    Model representing policy exemptions.
    
    Exemptions allow specific resources to be excluded from policy evaluation.
    """
    
    __tablename__ = "policy_exemptions"
    
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policies.id"),
        nullable=False,
        doc="ID of the policy"
    )
    
    resource_pattern: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Pattern matching resources to exempt"
    )
    
    exemption_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Reason for the exemption"
    )
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this exemption expires"
    )
    
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        doc="ID of the user who granted the exemption"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this exemption is active"
    )
    
    # Relationships
    policy: Mapped["Policy"] = relationship("Policy")
    
    def is_expired(self) -> bool:
        """Check if the exemption has expired."""
        if self.expires_at is None:
            return False
        return self.expires_at < datetime.utcnow()
    
    def is_valid(self) -> bool:
        """Check if the exemption is valid and active."""
        return self.is_active and not self.is_expired()