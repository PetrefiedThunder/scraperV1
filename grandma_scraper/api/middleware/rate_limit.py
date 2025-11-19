"""
Rate limiting middleware for API protection
"""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware.

    Limits requests per IP address to prevent abuse.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.rate_per_second = requests_per_minute / 60.0

        # Storage for rate limit buckets: {ip: {tokens: float, last_update: float}}
        self.buckets: Dict[str, Dict[str, float]] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def _get_tokens(self, ip: str, current_time: float) -> float:
        """Get available tokens for IP using token bucket algorithm"""
        if ip not in self.buckets:
            self.buckets[ip] = {
                "tokens": float(self.burst_size),
                "last_update": current_time
            }
            return self.burst_size

        bucket = self.buckets[ip]
        time_passed = current_time - bucket["last_update"]

        # Add tokens based on time passed
        bucket["tokens"] = min(
            self.burst_size,
            bucket["tokens"] + (time_passed * self.rate_per_second)
        )
        bucket["last_update"] = current_time

        return bucket["tokens"]

    def _consume_token(self, ip: str) -> bool:
        """Try to consume a token for the request"""
        if ip not in self.buckets:
            return False

        bucket = self.buckets[ip]
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            return True

        return False

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health check endpoint
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        ip = self._get_client_ip(request)
        current_time = time.time()

        # Get current token count
        tokens = self._get_tokens(ip, current_time)

        # Try to consume a token
        if not self._consume_token(ip):
            # Calculate retry-after time
            retry_after = int((1.0 - tokens) / self.rate_per_second) + 1

            logger.warning(
                f"Rate limit exceeded for IP {ip}",
                extra={
                    "ip": ip,
                    "path": request.url.path,
                    "retry_after": retry_after,
                }
            )

            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Content-Type": "application/json",
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)

        remaining = int(self.buckets[ip]["tokens"])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware to whitelist specific IP addresses (for admin endpoints).
    """

    def __init__(self, app, whitelist: Optional[list] = None, admin_paths: Optional[list] = None):
        super().__init__(app)
        self.whitelist = set(whitelist or [])
        self.admin_paths = admin_paths or ["/admin", "/api/v1/admin"]

    async def dispatch(self, request: Request, call_next):
        """Check IP whitelist for admin paths"""
        # Only check for admin paths
        if not any(request.url.path.startswith(path) for path in self.admin_paths):
            return await call_next(request)

        # Check if IP is whitelisted
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        if client_ip not in self.whitelist and "0.0.0.0" not in self.whitelist:
            logger.warning(
                f"Blocked admin access from non-whitelisted IP: {client_ip}",
                extra={"ip": client_ip, "path": request.url.path}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: IP not whitelisted"
            )

        return await call_next(request)
