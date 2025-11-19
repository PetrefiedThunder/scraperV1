"""
GZIP compression middleware for API responses
"""

import gzip
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.datastructures import Headers, MutableHeaders
import logging

logger = logging.getLogger(__name__)


class GZipMiddleware(BaseHTTPMiddleware):
    """
    Middleware to compress responses with GZIP.

    Compresses responses that:
    - Accept gzip encoding (from Accept-Encoding header)
    - Are larger than minimum_size bytes
    - Have compressible content types

    Args:
        app: ASGI application
        minimum_size: Minimum response size to compress (bytes)
        compressible_types: Set of content types to compress
        compression_level: GZIP compression level (1-9, default 6)
    """

    def __init__(
        self,
        app,
        minimum_size: int = 500,
        compressible_types: Optional[set] = None,
        compression_level: int = 6,
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level

        # Default compressible content types
        if compressible_types is None:
            compressible_types = {
                "text/html",
                "text/css",
                "text/plain",
                "text/xml",
                "text/javascript",
                "application/json",
                "application/javascript",
                "application/xml",
                "application/xhtml+xml",
                "application/rss+xml",
                "application/atom+xml",
                "image/svg+xml",
            }

        self.compressible_types = compressible_types

    def _should_compress(self, request: Request, response: Response) -> bool:
        """Determine if response should be compressed"""

        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return False

        # Check if already compressed
        if "content-encoding" in response.headers:
            return False

        # Check content type
        content_type = response.headers.get("content-type", "")
        # Extract base content type (before semicolon)
        base_type = content_type.split(";")[0].strip()

        if base_type not in self.compressible_types:
            return False

        return True

    async def dispatch(self, request: Request, call_next):
        """Process request and compress response if appropriate"""
        response = await call_next(request)

        # Don't compress if not appropriate
        if not self._should_compress(request, response):
            return response

        # For streaming responses, we need to read the body
        if isinstance(response, StreamingResponse):
            # Read streaming response
            body_parts = []
            async for chunk in response.body_iterator:
                body_parts.append(chunk)
            body = b"".join(body_parts)
        else:
            body = response.body

        # Check minimum size
        if len(body) < self.minimum_size:
            return response

        # Compress the body
        try:
            compressed_body = gzip.compress(body, compresslevel=self.compression_level)

            # Calculate compression ratio
            original_size = len(body)
            compressed_size = len(compressed_body)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            logger.debug(
                f"Compressed response: {original_size} -> {compressed_size} bytes ({ratio:.1f}% reduction)",
                extra={
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "ratio": ratio,
                }
            )

            # Create new response with compressed body
            headers = MutableHeaders(response.headers)
            headers["content-encoding"] = "gzip"
            headers["content-length"] = str(len(compressed_body))

            # Remove vary header if present and add gzip-specific vary
            if "vary" in headers:
                vary = headers["vary"]
                if "accept-encoding" not in vary.lower():
                    headers["vary"] = f"{vary}, Accept-Encoding"
            else:
                headers["vary"] = "Accept-Encoding"

            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=dict(headers),
                media_type=response.media_type,
            )

        except Exception as e:
            logger.error(f"Compression failed: {e}", exc_info=True)
            # Return original response on compression failure
            return response
