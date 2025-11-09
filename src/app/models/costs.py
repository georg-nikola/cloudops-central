"""
CloudOps Central Cost Management Models

This module contains database models for cost tracking, budgets,
alerts, and optimization recommendations.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, NamedModel


class CostPeriod(str, enum.Enum):
    """Enumeration of cost tracking periods."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AlertStatus(str, enum.Enum):
    """Enumeration of alert statuses."""

    ACTIVE = "active"
    TRIGGERED = "triggered"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertType(str, enum.Enum):
    """Enumeration of alert types."""

    BUDGET_THRESHOLD = "budget_threshold"
    COST_SPIKE = "cost_spike"
    COST_ANOMALY = "cost_anomaly"
    WASTE_DETECTION = "waste_detection"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"


class BudgetStatus(str, enum.Enum):
    """Enumeration of budget statuses."""

    ACTIVE = "active"
    EXCEEDED = "exceeded"
    WARNING = "warning"
    INACTIVE = "inactive"


class CostRecord(BaseModel):
    """
    Model representing cost records for infrastructure resources.

    This tracks actual costs incurred by cloud resources over time.
    """

    __tablename__ = "cost_records"

    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure_resources.id"),
        nullable=True,
        doc="ID of the infrastructure resource",
    )

    infrastructure_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructures.id"),
        nullable=True,
        doc="ID of the infrastructure",
    )

    cloud_provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cloud_providers.id"),
        nullable=False,
        doc="ID of the cloud provider",
    )

    service_name: Mapped[str] = mapped_column(
        String(200), nullable=False, doc="Name of the cloud service (EC2, S3, etc.)"
    )

    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False, doc="Type of resource generating the cost"
    )

    resource_identifier: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="External resource identifier"
    )

    region: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Cloud region"
    )

    cost_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, doc="Cost amount in USD"
    )

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", doc="Currency code"
    )

    billing_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, doc="Start of the billing period"
    )

    billing_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, doc="End of the billing period"
    )

    usage_quantity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 6), nullable=True, doc="Usage quantity for the period"
    )

    usage_unit: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="Unit of measurement for usage"
    )

    cost_details: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, doc="Detailed cost breakdown"
    )

    billing_account_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Cloud provider billing account ID"
    )

    project_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, doc="Cloud provider project/subscription ID"
    )

    # Relationships
    resource: Mapped[Optional["InfrastructureResource"]] = relationship(
        "InfrastructureResource"
    )

    infrastructure: Mapped[Optional["Infrastructure"]] = relationship("Infrastructure")

    cloud_provider: Mapped["CloudProvider"] = relationship("CloudProvider")


class CostBudget(NamedModel):
    """
    Model representing cost budgets for infrastructure.

    Budgets define spending limits and thresholds for cost management.
    """

    __tablename__ = "cost_budgets"

    budget_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, doc="Budget amount in USD"
    )

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", doc="Currency code"
    )

    period: Mapped[CostPeriod] = mapped_column(
        Enum(CostPeriod),
        nullable=False,
        default=CostPeriod.MONTHLY,
        doc="Budget period",
    )

    budget_status: Mapped[BudgetStatus] = mapped_column(
        Enum(BudgetStatus),
        nullable=False,
        default=BudgetStatus.ACTIVE,
        doc="Current budget status",
    )

    warning_threshold: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("80.0"),
        doc="Warning threshold percentage (0-100)",
    )

    critical_threshold: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.0"),
        doc="Critical threshold percentage (0-100)",
    )

    scope_filters: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, doc="Filters defining the budget scope"
    )

    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, doc="Budget start date"
    )

    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="Budget end date (null for ongoing)"
    )

    current_spend: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        doc="Current spending against this budget",
    )

    forecasted_spend: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, doc="Forecasted spending for the period"
    )

    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="Last time spending was updated",
    )

    notification_emails: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="Email addresses for budget notifications",
    )

    # Relationships
    alerts: Mapped[List["CostAlert"]] = relationship(
        "CostAlert", back_populates="budget", cascade="all, delete-orphan"
    )

    @property
    def spend_percentage(self) -> Decimal:
        """Calculate current spend as percentage of budget."""
        if self.budget_amount == 0:
            return Decimal("0")
        return (self.current_spend / self.budget_amount) * 100

    @property
    def remaining_budget(self) -> Decimal:
        """Calculate remaining budget amount."""
        return max(Decimal("0"), self.budget_amount - self.current_spend)

    def is_over_threshold(self, threshold: Decimal) -> bool:
        """Check if current spend exceeds a threshold percentage."""
        return self.spend_percentage >= threshold

    def is_warning_threshold_exceeded(self) -> bool:
        """Check if warning threshold is exceeded."""
        return self.is_over_threshold(self.warning_threshold)

    def is_critical_threshold_exceeded(self) -> bool:
        """Check if critical threshold is exceeded."""
        return self.is_over_threshold(self.critical_threshold)


class CostAlert(NamedModel):
    """
    Model representing cost-related alerts and notifications.

    Alerts notify users about budget thresholds, cost spikes, and anomalies.
    """

    __tablename__ = "cost_alerts"

    budget_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_budgets.id"),
        nullable=True,
        doc="ID of the related budget (if applicable)",
    )

    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType), nullable=False, doc="Type of alert"
    )

    alert_status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus),
        nullable=False,
        default=AlertStatus.ACTIVE,
        doc="Current alert status",
    )

    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", doc="Alert severity level"
    )

    threshold_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, doc="Threshold value that triggered the alert"
    )

    current_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True, doc="Current value that triggered the alert"
    )

    message: Mapped[str] = mapped_column(Text, nullable=False, doc="Alert message")

    alert_details: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, doc="Additional alert details"
    )

    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When the alert was triggered",
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="When the alert was resolved"
    )

    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, doc="ID of the user who resolved the alert"
    )

    notification_sent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, doc="Whether notification was sent"
    )

    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, doc="When notification was sent"
    )

    # Relationships
    budget: Mapped[Optional["CostBudget"]] = relationship(
        "CostBudget", back_populates="alerts"
    )

    def resolve(self, resolved_by: uuid.UUID) -> None:
        """Mark alert as resolved."""
        self.alert_status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by

    def suppress(self) -> None:
        """Suppress the alert."""
        self.alert_status = AlertStatus.SUPPRESSED


class CostOptimization(NamedModel):
    """
    Model representing cost optimization recommendations.

    This tracks opportunities to reduce costs through various optimizations.
    """

    __tablename__ = "cost_optimizations"

    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure_resources.id"),
        nullable=True,
        doc="ID of the target resource",
    )

    optimization_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Type of optimization (rightsizing, scheduling, etc.)",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Optimization category (compute, storage, network)",
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="medium",
        doc="Optimization priority (low, medium, high, critical)",
    )

    current_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, doc="Current monthly cost"
    )

    potential_savings: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, doc="Potential monthly savings"
    )

    savings_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, doc="Savings as percentage of current cost"
    )

    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0.5"),
        doc="Confidence score (0.0 to 1.0)",
    )

    recommendation: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Detailed optimization recommendation"
    )

    implementation_effort: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium", doc="Implementation effort level"
    )

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="low",
        doc="Risk level of implementing the optimization",
    )

    automation_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether automation is available for this optimization",
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When the optimization was detected",
    )

    last_validated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time the optimization was validated",
    )

    implemented_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the optimization was implemented",
    )

    implemented_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of the user who implemented the optimization",
    )

    actual_savings: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Actual savings realized after implementation",
    )

    optimization_details: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict, doc="Detailed optimization data and metrics"
    )

    # Relationships
    resource: Mapped[Optional["InfrastructureResource"]] = relationship(
        "InfrastructureResource"
    )

    @property
    def is_implemented(self) -> bool:
        """Check if optimization has been implemented."""
        return self.implemented_at is not None

    @property
    def annual_savings(self) -> Decimal:
        """Calculate potential annual savings."""
        return self.potential_savings * 12

    def implement(self, implemented_by: uuid.UUID) -> None:
        """Mark optimization as implemented."""
        self.implemented_at = datetime.utcnow()
        self.implemented_by = implemented_by
