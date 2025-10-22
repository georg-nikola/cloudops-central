"""
CloudOps Central Infrastructure Models

This module contains database models for infrastructure management,
including cloud providers, resources, templates, and resource types.
"""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, NamedModel


class CloudProviderType(str, enum.Enum):
    """Enumeration of supported cloud providers."""
    
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITAL_OCEAN = "digitalocean"
    LINODE = "linode"
    VULTR = "vultr"
    ON_PREMISE = "on_premise"


class ResourceStatus(str, enum.Enum):
    """Enumeration of resource statuses."""
    
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    STOPPING = "stopping"
    STARTING = "starting"
    TERMINATED = "terminated"
    TERMINATING = "terminating"
    ERROR = "error"
    UNKNOWN = "unknown"


class InfrastructureStatus(str, enum.Enum):
    """Enumeration of infrastructure statuses."""
    
    PLANNING = "planning"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    UPDATING = "updating"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    ERROR = "error"
    DRIFT_DETECTED = "drift_detected"


class CloudProvider(NamedModel):
    """
    Model representing a cloud provider configuration.
    
    This stores credentials and configuration for connecting to cloud providers.
    """
    
    __tablename__ = "cloud_providers"
    
    provider_type: Mapped[CloudProviderType] = mapped_column(
        Enum(CloudProviderType),
        nullable=False,
        doc="Type of cloud provider"
    )
    
    region: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Default region for this provider"
    )
    
    credentials: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Encrypted credentials for the provider"
    )
    
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Provider-specific configuration"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether this provider is active"
    )
    
    last_connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last successful connection timestamp"
    )
    
    connection_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unknown",
        doc="Current connection status"
    )
    
    # Relationships
    infrastructures: Mapped[List["Infrastructure"]] = relationship(
        "Infrastructure",
        back_populates="cloud_provider",
        cascade="all, delete-orphan"
    )
    
    resources: Mapped[List["InfrastructureResource"]] = relationship(
        "InfrastructureResource",
        back_populates="cloud_provider",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint('name', 'provider_type', name='unique_provider_name_type'),
    )


class ResourceType(NamedModel):
    """
    Model representing a type of infrastructure resource.
    
    This defines the schema and properties for different types of cloud resources.
    """
    
    __tablename__ = "resource_types"
    
    provider_type: Mapped[CloudProviderType] = mapped_column(
        Enum(CloudProviderType),
        nullable=False,
        doc="Cloud provider this resource type belongs to"
    )
    
    resource_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Category of the resource (compute, storage, network, etc.)"
    )
    
    terraform_type: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        doc="Terraform resource type identifier"
    )
    
    api_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="API version for this resource type"
    )
    
    schema_definition: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="JSON schema for resource configuration"
    )
    
    default_configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Default configuration values"
    )
    
    cost_model: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Cost calculation model for this resource type"
    )
    
    monitoring_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Monitoring and alerting configuration"
    )
    
    # Relationships
    resources: Mapped[List["InfrastructureResource"]] = relationship(
        "InfrastructureResource",
        back_populates="resource_type",
        cascade="all, delete-orphan"
    )
    
    templates: Mapped[List["InfrastructureTemplate"]] = relationship(
        "InfrastructureTemplate",
        secondary="template_resource_types",
        back_populates="resource_types"
    )


class Infrastructure(NamedModel):
    """
    Model representing a complete infrastructure deployment.
    
    This represents a collection of resources managed as a single unit.
    """
    
    __tablename__ = "infrastructures"
    
    cloud_provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cloud_providers.id"),
        nullable=False,
        doc="ID of the cloud provider"
    )
    
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure_templates.id"),
        nullable=True,
        doc="ID of the template used to create this infrastructure"
    )
    
    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Environment (dev, staging, prod, etc.)"
    )
    
    infrastructure_status: Mapped[InfrastructureStatus] = mapped_column(
        Enum(InfrastructureStatus),
        nullable=False,
        default=InfrastructureStatus.PLANNING,
        doc="Current infrastructure status"
    )
    
    terraform_state: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Terraform state information"
    )
    
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Infrastructure configuration"
    )
    
    variables: Mapped[Dict[str, str]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Terraform variables"
    )
    
    outputs: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Terraform outputs"
    )
    
    cost_estimate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Estimated monthly cost"
    )
    
    actual_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Actual monthly cost"
    )
    
    last_applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time infrastructure was applied"
    )
    
    last_drift_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time drift detection was run"
    )
    
    drift_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether configuration drift has been detected"
    )
    
    auto_apply: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether to automatically apply changes"
    )
    
    # Relationships
    cloud_provider: Mapped["CloudProvider"] = relationship(
        "CloudProvider",
        back_populates="infrastructures"
    )
    
    template: Mapped[Optional["InfrastructureTemplate"]] = relationship(
        "InfrastructureTemplate",
        back_populates="infrastructures"
    )
    
    resources: Mapped[List["InfrastructureResource"]] = relationship(
        "InfrastructureResource",
        back_populates="infrastructure",
        cascade="all, delete-orphan"
    )


class InfrastructureResource(NamedModel):
    """
    Model representing an individual infrastructure resource.
    
    This represents a single cloud resource (VM, database, storage, etc.).
    """
    
    __tablename__ = "infrastructure_resources"
    
    infrastructure_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructures.id"),
        nullable=True,
        doc="ID of the parent infrastructure"
    )
    
    cloud_provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cloud_providers.id"),
        nullable=False,
        doc="ID of the cloud provider"
    )
    
    resource_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource_types.id"),
        nullable=False,
        doc="ID of the resource type"
    )
    
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="External resource ID from the cloud provider"
    )
    
    region: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Cloud region where the resource is deployed"
    )
    
    availability_zone: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Availability zone where the resource is deployed"
    )
    
    resource_status: Mapped[ResourceStatus] = mapped_column(
        Enum(ResourceStatus),
        nullable=False,
        default=ResourceStatus.UNKNOWN,
        doc="Current resource status"
    )
    
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Resource configuration"
    )
    
    desired_configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Desired resource configuration"
    )
    
    actual_configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Actual resource configuration from provider"
    )
    
    cost_per_hour: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        doc="Cost per hour for this resource"
    )
    
    monthly_cost_estimate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Estimated monthly cost"
    )
    
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time resource was synced with provider"
    )
    
    sync_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Last sync error message"
    )
    
    # Relationships
    infrastructure: Mapped[Optional["Infrastructure"]] = relationship(
        "Infrastructure",
        back_populates="resources"
    )
    
    cloud_provider: Mapped["CloudProvider"] = relationship(
        "CloudProvider",
        back_populates="resources"
    )
    
    resource_type: Mapped["ResourceType"] = relationship(
        "ResourceType",
        back_populates="resources"
    )


class InfrastructureTemplate(NamedModel):
    """
    Model representing a reusable infrastructure template.
    
    This allows creating standardized infrastructure patterns.
    """
    
    __tablename__ = "infrastructure_templates"
    
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        doc="Template version"
    )
    
    provider_type: Mapped[CloudProviderType] = mapped_column(
        Enum(CloudProviderType),
        nullable=False,
        doc="Target cloud provider"
    )
    
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Template category (web-app, database, etc.)"
    )
    
    terraform_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Terraform configuration code"
    )
    
    variables_schema: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Schema for template variables"
    )
    
    default_variables: Mapped[Dict[str, str]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Default variable values"
    )
    
    cost_estimate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Base cost estimate for this template"
    )
    
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether this template is publicly available"
    )
    
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of times this template has been used"
    )
    
    # Relationships
    infrastructures: Mapped[List["Infrastructure"]] = relationship(
        "Infrastructure",
        back_populates="template",
        cascade="all, delete-orphan"
    )
    
    resource_types: Mapped[List["ResourceType"]] = relationship(
        "ResourceType",
        secondary="template_resource_types",
        back_populates="templates"
    )


# Association table for many-to-many relationship between templates and resource types
template_resource_types = Table(
    "template_resource_types",
    Base.metadata,
    Column("template_id", UUID(as_uuid=True), ForeignKey("infrastructure_templates.id"), primary_key=True),
    Column("resource_type_id", UUID(as_uuid=True), ForeignKey("resource_types.id"), primary_key=True),
)