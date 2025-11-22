"""Rate limiting middleware for API endpoints."""

import time
from collections import defaultdict
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# In-memory rate limit storage (use Redis in production)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


class RateLimiter:
    """Simple rate limiter using sliding window algorithm."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day

    def _cleanup_old_entries(self, key: str, window_seconds: int) -> None:
        """Remove entries older than the window."""
        now = time.time()
        _rate_limit_store[key] = [
            timestamp
            for timestamp in _rate_limit_store[key]
            if now - timestamp < window_seconds
        ]

    def _check_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is within rate limit."""
        self._cleanup_old_entries(key, window_seconds)
        return len(_rate_limit_store[key]) < limit

    def _record_request(self, key: str) -> None:
        """Record a request."""
        _rate_limit_store[key].append(time.time())

    def is_allowed(
        self,
        identifier: str,
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed.
        
        Returns:
            (is_allowed, error_message)
        """
        # Use instance defaults if not specified
        rpm = requests_per_minute or self.requests_per_minute
        rph = requests_per_hour or self.requests_per_hour
        rpd = requests_per_day or self.requests_per_day

        # Check minute limit
        if not self._check_limit(f"{identifier}:minute", rpm, 60):
            return False, f"Rate limit exceeded: {rpm} requests per minute"

        # Check hour limit
        if not self._check_limit(f"{identifier}:hour", rph, 3600):
            return False, f"Rate limit exceeded: {rph} requests per hour"

        # Check day limit
        if not self._check_limit(f"{identifier}:day", rpd, 86400):
            return False, f"Rate limit exceeded: {rpd} requests per day"

        # Record request
        self._record_request(f"{identifier}:minute")
        self._record_request(f"{identifier}:hour")
        self._record_request(f"{identifier}:day")

        return True, None


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def get_client_identifier(request: Request) -> str:
    """Get a unique identifier for rate limiting (user ID or IP address)."""
    # Try to get user ID from auth token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # In a real implementation, decode the JWT to get user_id
        # For now, use the token itself as identifier
        token = auth_header.replace("Bearer ", "")
        # Use first 16 chars as identifier (in production, decode JWT)
        return f"user:{token[:16]}"
    
    # Fall back to IP address
    client_ip = request.client.host if request.client else "unknown"
    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to all requests."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/healthz", "/api/v1/health"]:
            return await call_next(request)

        identifier = get_client_identifier(request)
        rate_limiter = get_rate_limiter()

        is_allowed, error_message = rate_limiter.is_allowed(identifier)
        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": error_message},
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        return response

