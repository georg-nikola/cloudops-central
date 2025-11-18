"""
Unit tests for custom exceptions.
"""

from datetime import datetime

import pytest

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CloudOpsException,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
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
    """Test DatabaseError."""

    @pytest.mark.unit
    def test_database_exception(self):
        """Test database exception creation."""
        exc = DatabaseError(
            message="Database connection failed",
            details={"host": "localhost", "port": 5432},
        )

        assert exc.message == "Database connection failed"
        assert exc.error_type == "database_error"
        assert exc.status_code == 500
        assert exc.details["host"] == "localhost"


class TestValidationException:
    """Test ValidationError."""

    @pytest.mark.unit
    def test_validation_exception(self):
        """Test validation exception creation."""
        exc = ValidationError(
            message="Invalid email format",
            field="email",
            value="invalid-email",
        )

        assert exc.message == "Invalid email format"
        assert exc.error_type == "validation_error"
        assert exc.status_code == 400
        assert exc.details["field"] == "email"


class TestAuthenticationException:
    """Test AuthenticationError."""

    @pytest.mark.unit
    def test_authentication_exception(self):
        """Test authentication exception creation."""
        exc = AuthenticationError(
            message="Invalid credentials",
        )

        assert exc.message == "Invalid credentials"
        assert exc.error_type == "authentication_error"
        assert exc.status_code == 401


class TestAuthorizationException:
    """Test AuthorizationError."""

    @pytest.mark.unit
    def test_authorization_exception(self):
        """Test authorization exception creation."""
        exc = AuthorizationError(
            message="Insufficient permissions",
            required_permission="admin",
        )

        assert exc.message == "Insufficient permissions"
        assert exc.error_type == "authorization_error"
        assert exc.status_code == 403
        assert exc.details["required_permission"] == "admin"


class TestResourceNotFoundException:
    """Test NotFoundError."""

    @pytest.mark.unit
    def test_resource_not_found_exception(self):
        """Test resource not found exception creation."""
        exc = NotFoundError(
            resource_type="user",
            resource_id="123",
        )

        assert "user" in exc.message
        assert exc.error_type == "not_found_error"
        assert exc.status_code == 404
        assert exc.details["resource_type"] == "user"


class TestResourceConflictException:
    """Test ConflictError."""

    @pytest.mark.unit
    def test_resource_conflict_exception(self):
        """Test resource conflict exception creation."""
        exc = ConflictError(
            message="Resource already exists",
            resource_type="user",
        )

        assert exc.message == "Resource already exists"
        assert exc.error_type == "conflict_error"
        assert exc.status_code == 409


class TestExternalServiceException:
    """Test ExternalServiceError."""

    @pytest.mark.unit
    def test_external_service_exception(self):
        """Test external service exception creation."""
        exc = ExternalServiceError(
            service_name="AWS",
            message="API call failed",
        )

        assert "AWS" in exc.message
        assert exc.error_type == "external_service_error"
        assert exc.status_code == 502
        assert exc.details["service_name"] == "AWS"
