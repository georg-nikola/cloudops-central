"""
Unit tests for custom exceptions.
"""

from datetime import datetime

import pytest

from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    CloudOpsException,
    DatabaseException,
    ExternalServiceException,
    ResourceConflictException,
    ResourceNotFoundException,
    ValidationException,
)


class TestCloudOpsException:
    """Test base CloudOpsException class."""

    @pytest.mark.unit
    def test_basic_exception(self):
        """Test creating a basic exception."""
        exc = CloudOpsException(
            message="Test error",
            error_type="test_error",
            status_code=500,
        )

        assert exc.message == "Test error"
        assert exc.error_type == "test_error"
        assert exc.status_code == 500
        assert exc.details is None
        assert isinstance(exc.timestamp, datetime)

    @pytest.mark.unit
    def test_exception_with_details(self):
        """Test exception with additional details."""
        details = {"field": "value", "code": 123}
        exc = CloudOpsException(
            message="Test error",
            error_type="test_error",
            status_code=400,
            details=details,
        )

        assert exc.details == details
        assert exc.details["field"] == "value"

    @pytest.mark.unit
    def test_exception_str_representation(self):
        """Test string representation of exception."""
        exc = CloudOpsException(
            message="Test error",
            error_type="test_error",
        )

        str_repr = str(exc)
        assert "Test error" in str_repr


class TestDatabaseException:
    """Test DatabaseException."""

    @pytest.mark.unit
    def test_database_exception(self):
        """Test database exception creation."""
        exc = DatabaseException(
            message="Database connection failed",
            details={"host": "localhost", "port": 5432},
        )

        assert exc.message == "Database connection failed"
        assert exc.error_type == "database_error"
        assert exc.status_code == 500
        assert exc.details["host"] == "localhost"


class TestValidationException:
    """Test ValidationException."""

    @pytest.mark.unit
    def test_validation_exception(self):
        """Test validation exception creation."""
        exc = ValidationException(
            message="Invalid email format",
            details={"field": "email", "value": "invalid-email"},
        )

        assert exc.message == "Invalid email format"
        assert exc.error_type == "validation_error"
        assert exc.status_code == 422
        assert exc.details["field"] == "email"


class TestAuthenticationException:
    """Test AuthenticationException."""

    @pytest.mark.unit
    def test_authentication_exception(self):
        """Test authentication exception creation."""
        exc = AuthenticationException(
            message="Invalid credentials",
        )

        assert exc.message == "Invalid credentials"
        assert exc.error_type == "authentication_error"
        assert exc.status_code == 401


class TestAuthorizationException:
    """Test AuthorizationException."""

    @pytest.mark.unit
    def test_authorization_exception(self):
        """Test authorization exception creation."""
        exc = AuthorizationException(
            message="Insufficient permissions",
            details={"required_role": "admin"},
        )

        assert exc.message == "Insufficient permissions"
        assert exc.error_type == "authorization_error"
        assert exc.status_code == 403
        assert exc.details["required_role"] == "admin"


class TestResourceNotFoundException:
    """Test ResourceNotFoundException."""

    @pytest.mark.unit
    def test_resource_not_found_exception(self):
        """Test resource not found exception creation."""
        exc = ResourceNotFoundException(
            message="Resource not found",
            details={"resource_type": "user", "resource_id": "123"},
        )

        assert exc.message == "Resource not found"
        assert exc.error_type == "resource_not_found"
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "user"


class TestResourceConflictException:
    """Test ResourceConflictException."""

    @pytest.mark.unit
    def test_resource_conflict_exception(self):
        """Test resource conflict exception creation."""
        exc = ResourceConflictException(
            message="Resource already exists",
            details={"resource_type": "user", "email": "test@example.com"},
        )

        assert exc.message == "Resource already exists"
        assert exc.error_type == "resource_conflict"
        assert exc.status_code == 409


class TestExternalServiceException:
    """Test ExternalServiceException."""

    @pytest.mark.unit
    def test_external_service_exception(self):
        """Test external service exception creation."""
        exc = ExternalServiceException(
            message="AWS API call failed",
            details={"service": "EC2", "operation": "DescribeInstances"},
        )

        assert exc.message == "AWS API call failed"
        assert exc.error_type == "external_service_error"
        assert exc.status_code == 502
        assert exc.details["service"] == "EC2"
