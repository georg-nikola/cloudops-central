"""
CloudOps Central Logging Configuration

This module provides structured logging configuration with support for
JSON formatting, correlation IDs, and different log levels for production
and development environments.
"""

import logging
import logging.config
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

from app.core.config import get_settings

settings = get_settings()


def configure_structlog() -> None:
    """Configure structlog for structured logging."""

    # Determine if we're in development mode
    is_dev = settings.is_development()

    # Configure processors based on environment
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_dev:
        # Development: Pretty console output
        processors.extend([structlog.dev.ConsoleRenderer(colors=True)])
    else:
        # Production: JSON output
        processors.extend(
            [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_logging() -> structlog.BoundLogger:
    """
    Setup logging configuration for the application.

    Returns:
        Configured logger instance
    """

    # Configure structlog
    configure_structlog()

    # Configure standard library logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
            },
            "console": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console" if settings.is_development() else "json",
                "stream": sys.stdout,
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING" if not settings.DEBUG else "INFO",
                "propagate": False,
            },
            "alembic": {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
    }

    # Add file handler if log file is specified
    if settings.LOG_FILE:
        logging_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": settings.LOG_FILE,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        }

        # Add file handler to all loggers
        for logger_config in logging_config["loggers"].values():
            logger_config["handlers"].append("file")

    # Apply logging configuration
    logging.config.dictConfig(logging_config)

    # Get the main application logger
    logger = get_logger("cloudops-central")
    logger.info(
        "Logging configured",
        log_level=settings.LOG_LEVEL,
        environment=settings.ENVIRONMENT,
    )

    return logger


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


class LoggingMiddleware:
    """
    Middleware for request/response logging with correlation IDs.
    """

    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or get_logger("middleware.logging")

    async def __call__(self, request, call_next):
        """Process request and log details."""
        import uuid

        from starlette.middleware.base import BaseHTTPMiddleware

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Add correlation ID to context
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=correlation_id,
        )

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id

        # Log request
        self.logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            client_ip=request.client.host if request.client else None,
        )

        # Process request
        import time

        start_time = time.time()

        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log successful response
            self.logger.info(
                "Request completed",
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as exc:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            self.logger.error(
                "Request failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=round(duration * 1000, 2),
                exc_info=True,
            )

            # Re-raise the exception
            raise


class AuditLogger:
    """
    Specialized logger for audit events.
    """

    def __init__(self):
        self.logger = get_logger("audit")

    def log_event(
        self,
        event_type: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event (create, update, delete, etc.)
            action: Specific action performed
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            user_id: ID of the user who performed the action
            details: Additional event details
            **kwargs: Additional fields to log
        """
        log_data = {
            "event_type": event_type,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "details": details or {},
            **kwargs,
        }

        self.logger.info("Audit event", **log_data)

    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = "medium",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Log a security-related event.

        Args:
            event_type: Type of security event
            description: Description of the event
            severity: Severity level (low, medium, high, critical)
            user_id: ID of the user involved
            ip_address: IP address of the client
            **kwargs: Additional fields to log
        """
        log_data = {
            "event_category": "security",
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "user_id": user_id,
            "ip_address": ip_address,
            **kwargs,
        }

        self.logger.warning("Security event", **log_data)


class PerformanceLogger:
    """
    Logger for performance metrics and monitoring.
    """

    def __init__(self):
        self.logger = get_logger("performance")

    def log_database_query(
        self, query: str, duration_ms: float, rows_affected: Optional[int] = None, **kwargs
    ) -> None:
        """
        Log database query performance.

        Args:
            query: SQL query or operation description
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
            **kwargs: Additional fields to log
        """
        self.logger.info(
            "Database query",
            query=query,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            **kwargs,
        )

    def log_api_call(
        self,
        service: str,
        endpoint: str,
        duration_ms: float,
        status_code: Optional[int] = None,
        **kwargs,
    ) -> None:
        """
        Log external API call performance.

        Args:
            service: Name of the external service
            endpoint: API endpoint called
            duration_ms: Call duration in milliseconds
            status_code: HTTP status code returned
            **kwargs: Additional fields to log
        """
        self.logger.info(
            "API call",
            service=service,
            endpoint=endpoint,
            duration_ms=duration_ms,
            status_code=status_code,
            **kwargs,
        )

    def log_task_execution(
        self, task_name: str, duration_ms: float, status: str = "success", **kwargs
    ) -> None:
        """
        Log background task execution.

        Args:
            task_name: Name of the task
            duration_ms: Task duration in milliseconds
            status: Task execution status
            **kwargs: Additional fields to log
        """
        self.logger.info(
            "Task execution", task_name=task_name, duration_ms=duration_ms, status=status, **kwargs
        )


# Global logger instances
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()
