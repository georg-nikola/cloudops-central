"""
CloudOps Central Middleware

This module contains custom middleware for the CloudOps Central application,
including authentication, rate limiting, security headers, and logging.
"""

import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, RateLimitExceededError
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    This middleware adds standard security headers to protect against
    common web vulnerabilities.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP header
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging with correlation IDs.
    
    This middleware logs all incoming requests and outgoing responses
    with correlation IDs for request tracing.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware.logging")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id
        
        # Start timer
        start_time = time.time()
        
        # Log request
        self.logger.info(
            "Request started",
            correlation_id=correlation_id,
            method=request.method,
            url=str(request.url),
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log successful response
            self.logger.info(
                "Request completed",
                correlation_id=correlation_id,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as exc:
            # Calculate duration
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log error
            self.logger.error(
                "Request failed",
                correlation_id=correlation_id,
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=duration_ms,
                exc_info=True
            )
            
            # Re-raise the exception
            raise
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if request.client:
            return request.client.host
        
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using a simple in-memory store.
    
    For production use, this should be replaced with a Redis-based
    rate limiter for distributed environments.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware.rate_limit")
        self.requests = {}  # Simple in-memory store
        self.window_size = 60  # 1 minute window
        self.max_requests = settings.RATE_LIMIT_PER_MINUTE
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting based on client IP."""
        client_ip = self._get_client_ip(request)
        
        if not client_ip:
            # If we can't determine IP, allow the request
            return await call_next(request)
        
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            self.logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                limit=self.max_requests,
                window=self.window_size
            )
            
            # Return rate limit error
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "type": "rate_limit_exceeded",
                        "message": "Too many requests",
                        "details": {
                            "limit": self.max_requests,
                            "window": self.window_size,
                            "retry_after": 60
                        }
                    }
                },
                headers={"Retry-After": "60"}
            )
        
        # Record the request
        self._record_request(client_ip, current_time)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if request.client:
            return request.client.host
        
        return None
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Remove entries older than the window size."""
        cutoff_time = current_time - self.window_size
        
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                timestamp for timestamp in self.requests[ip]
                if timestamp > cutoff_time
            ]
            
            # Remove empty entries
            if not self.requests[ip]:
                del self.requests[ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if the client IP is rate limited."""
        if client_ip not in self.requests:
            return False
        
        request_count = len(self.requests[client_ip])
        return request_count >= self.max_requests
    
    def _record_request(self, client_ip: str, current_time: float) -> None:
        """Record a request for the client IP."""
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        self.requests[client_ip].append(current_time)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for JWT token validation.
    
    This middleware validates JWT tokens for protected endpoints
    and sets user information in the request state.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware.auth")
        
        # Endpoints that don't require authentication
        self.public_paths = {
            "/",
            "/health",
            "/api/v1/docs",
            "/api/v1/redoc",
            "/api/v1/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate authentication for protected endpoints."""
        path = request.url.path
        
        # Skip authentication for public paths
        if self._is_public_path(path):
            return await call_next(request)
        
        # Skip authentication for static files
        if path.startswith("/static/"):
            return await call_next(request)
        
        # Extract and validate token
        try:
            token = self._extract_token(request)
            if not token:
                raise AuthenticationError("No authentication token provided")
            
            # Validate token and get user info
            user_info = await self._validate_token(token)
            
            # Set user information in request state
            request.state.user = user_info
            request.state.user_id = user_info.get("user_id")
            
            self.logger.debug(
                "Authentication successful",
                user_id=user_info.get("user_id"),
                path=path
            )
            
        except AuthenticationError as exc:
            self.logger.warning(
                "Authentication failed",
                path=path,
                error=str(exc)
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=exc.to_dict(),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if the path is public and doesn't require authentication."""
        return path in self.public_paths
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return None
        
        if not authorization.startswith("Bearer "):
            return None
        
        return authorization.split(" ", 1)[1]
    
    async def _validate_token(self, token: str) -> dict:
        """
        Validate JWT token and return user information.
        
        This is a placeholder implementation. In a real application,
        this would validate the JWT token and return user information.
        """
        # TODO: Implement actual JWT validation
        # For now, return a mock user for development
        if settings.is_development() and token == "dev-token":
            return {
                "user_id": "dev-user-id",
                "email": "dev@example.com",
                "roles": ["admin"]
            }
        
        # Import here to avoid circular imports
        from app.services.auth import AuthService
        
        auth_service = AuthService()
        return await auth_service.validate_token(token)


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with additional security features.
    
    This extends the standard CORS middleware with additional
    security checks and logging.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware.cors")
        self.allowed_origins = settings.BACKEND_CORS_ORIGINS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS requests with security logging."""
        origin = request.headers.get("origin")
        
        # Log CORS requests for security monitoring
        if origin:
            is_allowed = origin in self.allowed_origins
            self.logger.info(
                "CORS request",
                origin=origin,
                method=request.method,
                path=request.url.path,
                allowed=is_allowed
            )
            
            if not is_allowed:
                self.logger.warning(
                    "CORS request from unauthorized origin",
                    origin=origin,
                    path=request.url.path
                )
        
        response = await call_next(request)
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting request metrics.
    
    This middleware collects metrics about request duration,
    status codes, and other performance indicators.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware.metrics")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect request metrics."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate metrics
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log metrics
            self.logger.info(
                "Request metrics",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                response_size=response.headers.get("content-length", 0)
            )
            
            # TODO: Send metrics to monitoring system (Prometheus, etc.)
            
            return response
            
        except Exception as exc:
            # Log error metrics
            duration_ms = round((time.time() - start_time) * 1000, 2)
            
            self.logger.error(
                "Request error metrics",
                method=request.method,
                path=request.url.path,
                error_type=type(exc).__name__,
                duration_ms=duration_ms
            )
            
            raise