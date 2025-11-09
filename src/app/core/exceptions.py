"""
CloudOps Central Custom Exceptions

This module defines custom exceptions used throughout the CloudOps Central application
with proper error codes, messages, and structured error responses.
"""

from datetime import datetime
from typing import Any, Dict, Optional


class CloudOpsException(Exception):
    """
    Base exception class for CloudOps Central application.

    All custom exceptions should inherit from this class to ensure
    consistent error handling and logging.
    """

    def __init__(
        self,
        message: str,
        error_type: str = "cloudops_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ):
        """
        Initialize CloudOps exception.

        Args:
            message: Technical error message for logging
            error_type: Error type identifier
            status_code: HTTP status code
            details: Additional error details
            user_message: User-friendly error message
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or message
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.user_message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
            }
        }


class ValidationError(CloudOpsException):
    """Exception raised for validation errors."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            error_type="validation_error",
            status_code=400,
            details=details,
            user_message=f"Validation failed: {message}",
        )


class AuthenticationError(CloudOpsException):
    """Exception raised for authentication failures."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_type="authentication_error",
            status_code=401,
            details=details,
            user_message="Authentication required",
        )


class AuthorizationError(CloudOpsException):
    """Exception raised for authorization failures."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if required_permission:
            details["required_permission"] = required_permission
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_type="authorization_error",
            status_code=403,
            details=details,
            user_message="Access denied",
        )


class NotFoundError(CloudOpsException):
    """Exception raised when a resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"

        super().__init__(
            message=message,
            error_type="not_found_error",
            status_code=404,
            details=details,
            user_message=f"The requested {resource_type} could not be found",
        )


class ConflictError(CloudOpsException):
    """Exception raised for resource conflicts."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_type="conflict_error",
            status_code=409,
            details=details,
            user_message=f"Conflict: {message}",
        )


class ExternalServiceError(CloudOpsException):
    """Exception raised for external service failures."""

    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["service_name"] = service_name
        if status_code:
            details["external_status_code"] = status_code
        if response_data:
            details["response_data"] = response_data

        super().__init__(
            message=f"{service_name} error: {message}",
            error_type="external_service_error",
            status_code=502,
            details=details,
            user_message=f"External service temporarily unavailable: {service_name}",
        )


class InfrastructureError(CloudOpsException):
    """Exception raised for infrastructure-related errors."""

    def __init__(
        self,
        message: str,
        infrastructure_id: Optional[str] = None,
        provider: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if infrastructure_id:
            details["infrastructure_id"] = infrastructure_id
        if provider:
            details["provider"] = provider
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_type="infrastructure_error",
            status_code=500,
            details=details,
            user_message="Infrastructure operation failed",
        )


class PolicyViolationError(CloudOpsException):
    """Exception raised for policy violations."""

    def __init__(
        self,
        policy_name: str,
        violation_message: str,
        policy_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["policy_name"] = policy_name
        details["violation_message"] = violation_message
        if policy_id:
            details["policy_id"] = policy_id
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=f"Policy violation: {policy_name} - {violation_message}",
            error_type="policy_violation_error",
            status_code=400,
            details=details,
            user_message=f"Policy violation: {violation_message}",
        )


class CostLimitExceededError(CloudOpsException):
    """Exception raised when cost limits are exceeded."""

    def __init__(
        self,
        budget_name: str,
        current_cost: float,
        budget_limit: float,
        currency: str = "USD",
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details.update(
            {
                "budget_name": budget_name,
                "current_cost": current_cost,
                "budget_limit": budget_limit,
                "currency": currency,
                "percentage": round((current_cost / budget_limit) * 100, 2),
            }
        )

        super().__init__(
            message=f"Cost limit exceeded for budget '{budget_name}': "
            f"{current_cost} {currency} > {budget_limit} {currency}",
            error_type="cost_limit_exceeded_error",
            status_code=402,
            details=details,
            user_message=f"Budget limit exceeded for '{budget_name}'",
        )


class RateLimitExceededError(CloudOpsException):
    """Exception raised when rate limits are exceeded."""

    def __init__(
        self,
        limit: int,
        window: int,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details.update({"limit": limit, "window": window, "retry_after": retry_after})

        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window} seconds",
            error_type="rate_limit_exceeded_error",
            status_code=429,
            details=details,
            user_message="Too many requests. Please try again later.",
        )


class ConfigurationError(CloudOpsException):
    """Exception raised for configuration errors."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            error_type="configuration_error",
            status_code=500,
            details=details,
            user_message="System configuration error",
        )


class DatabaseError(CloudOpsException):
    """Exception raised for database-related errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table

        super().__init__(
            message=message,
            error_type="database_error",
            status_code=500,
            details=details,
            user_message="Database operation failed",
        )


class TerraformError(CloudOpsException):
    """Exception raised for Terraform-related errors."""

    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if command:
            details["command"] = command
        if exit_code is not None:
            details["exit_code"] = exit_code
        if stdout:
            details["stdout"] = stdout
        if stderr:
            details["stderr"] = stderr

        super().__init__(
            message=message,
            error_type="terraform_error",
            status_code=500,
            details=details,
            user_message="Infrastructure deployment failed",
        )


class CloudProviderError(CloudOpsException):
    """Exception raised for cloud provider API errors."""

    def __init__(
        self,
        provider: str,
        message: str,
        error_code: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details["provider"] = provider
        if error_code:
            details["provider_error_code"] = error_code
        if operation:
            details["operation"] = operation

        super().__init__(
            message=f"{provider} error: {message}",
            error_type="cloud_provider_error",
            status_code=502,
            details=details,
            user_message=f"Cloud provider error ({provider})",
        )


# Convenience functions for raising common exceptions
def raise_not_found(resource_type: str, resource_id: Optional[str] = None) -> None:
    """Raise a NotFoundError with the given parameters."""
    raise NotFoundError(resource_type, resource_id)


def raise_validation_error(message: str, field: Optional[str] = None) -> None:
    """Raise a ValidationError with the given parameters."""
    raise ValidationError(message, field)


def raise_authorization_error(
    message: str = "Insufficient permissions", required_permission: Optional[str] = None
) -> None:
    """Raise an AuthorizationError with the given parameters."""
    raise AuthorizationError(message, required_permission)


def raise_conflict_error(message: str, resource_type: Optional[str] = None) -> None:
    """Raise a ConflictError with the given parameters."""
    raise ConflictError(message, resource_type)
