"""
Robots.txt checker for ethical scraping.

Respects website's robots.txt directives.
"""

import asyncio
from typing import Dict, Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import httpx

from grandma_scraper.utils.url_validator import validate_url_ssrf


class RobotsChecker:
    """
    Checks and respects robots.txt directives.

    Caches robots.txt files per domain for efficiency.
    """

    def __init__(self, user_agent: str = "*"):
        """
        Initialize robots checker.

        Args:
            user_agent: User agent to check permissions for
        """
        self.user_agent = user_agent
        self._cache: Dict[str, RobotFileParser] = {}
        self._lock = asyncio.Lock()

    async def can_fetch(self, url: str) -> tuple[bool, Optional[str]]:
        """
        Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            Tuple of (allowed: bool, reason: str or None)
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Get or fetch robots.txt for this domain
        parser = await self._get_robots_parser(domain)

        if parser is None:
            # No robots.txt or error fetching - allow by default
            return True, None

        # Check if URL is allowed
        allowed = parser.can_fetch(self.user_agent, url)

        if not allowed:
            reason = f"Disallowed by robots.txt for user-agent '{self.user_agent}'"
            return False, reason

        return True, None

    async def _get_robots_parser(self, domain: str) -> Optional[RobotFileParser]:
        """
        Get robots.txt parser for domain (cached).

        Args:
            domain: Base domain URL

        Returns:
            RobotFileParser or None if not available
        """
        async with self._lock:
            # Check cache
            if domain in self._cache:
                return self._cache[domain]

            # Fetch robots.txt
            robots_url = urljoin(domain, "/robots.txt")

            # Validate robots.txt URL against SSRF
            is_valid, error_msg = validate_url_ssrf(robots_url)
            if not is_valid:
                # Treat invalid robots.txt URL as no robots.txt
                self._cache[domain] = None
                return None

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(robots_url)

                    if response.status_code == 200:
                        parser = RobotFileParser()
                        parser.parse(response.text.splitlines())
                        self._cache[domain] = parser
                        return parser
                    else:
                        # No robots.txt - allow all
                        self._cache[domain] = None
                        return None

            except Exception:
                # Error fetching - allow by default
                self._cache[domain] = None
                return None

    def clear_cache(self) -> None:
        """Clear robots.txt cache."""
        self._cache.clear()
