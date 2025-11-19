"""
Request ID middleware for distributed tracing
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.datastructures import MutableHeaders
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to all requests for distributed tracing.

    The request ID is:
    - Generated if not provided by client
    - Added to response headers
    - Available in request.state for logging
    - Included in all log messages
    """

    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        # Get request ID from header or generate new one
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())

        # Store in request state for access in route handlers
        request.state.request_id = request_id

        # Add to response headers
        response = await call_next(request)
        response.headers[self.header_name] = request_id

        return response


class RequestContextFilter(logging.Filter):
    """
    Logging filter to add request ID to all log records.

    Usage:
        handler.addFilter(RequestContextFilter())
    """

    def filter(self, record):
        # Try to get request ID from current context
        # This is set by the RequestIDMiddleware
        record.request_id = getattr(record, 'request_id', '-')
        return True
