"""
Monitoring and metrics setup for CloudOps Central.
Provides Prometheus metrics integration.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Application metrics
api_requests_total = Counter(
    "cloudops_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

api_request_duration = Histogram(
    "cloudops_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
)

infrastructure_resources_total = Gauge(
    "cloudops_infrastructure_resources_total",
    "Total infrastructure resources",
    ["cloud_provider", "resource_type"],
)

cost_monthly_total = Gauge(
    "cloudops_cost_monthly_total_dollars",
    "Total monthly cost in dollars",
    ["cloud_provider", "service"],
)

policy_violations_total = Counter(
    "cloudops_policy_violations_total",
    "Total policy violations detected",
    ["policy_name", "severity"],
)

drift_detections_total = Counter(
    "cloudops_drift_detections_total",
    "Total drift detections",
    ["resource_type", "cloud_provider"],
)

app_info = Info("cloudops_central", "CloudOps Central application information")


async def setup_monitoring() -> None:
    """
    Initialize monitoring and metrics collection.
    Sets up Prometheus metrics and application info.
    """
    logger.info("Setting up monitoring and metrics")

    # Set application info
    app_info.info(
        {"version": "1.0.0", "environment": "production", "service": "cloudops-central"}
    )

    logger.info("Monitoring setup complete")


def record_api_request(
    method: str, endpoint: str, status: int, duration: float
) -> None:
    """Record API request metrics."""
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)


def update_infrastructure_metrics(
    cloud_provider: str, resource_type: str, count: int
) -> None:
    """Update infrastructure resource metrics."""
    infrastructure_resources_total.labels(
        cloud_provider=cloud_provider, resource_type=resource_type
    ).set(count)


def update_cost_metrics(cloud_provider: str, service: str, amount: float) -> None:
    """Update cost metrics."""
    cost_monthly_total.labels(cloud_provider=cloud_provider, service=service).set(
        amount
    )


def record_policy_violation(policy_name: str, severity: str) -> None:
    """Record policy violation."""
    policy_violations_total.labels(policy_name=policy_name, severity=severity).inc()


def record_drift_detection(resource_type: str, cloud_provider: str) -> None:
    """Record drift detection."""
    drift_detections_total.labels(
        resource_type=resource_type, cloud_provider=cloud_provider
    ).inc()
