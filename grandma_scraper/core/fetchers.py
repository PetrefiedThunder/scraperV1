"""
HTML fetchers for retrieving web page content.

Provides abstraction over different fetching strategies:
- RequestsFetcher: Fast, for static HTML
- BrowserFetcher: Slower, handles JavaScript (using Playwright)
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional, List
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, PlaywrightContextManager

from grandma_scraper.utils.url_validator import validate_url_ssrf


class HTMLDocument:
    """Wrapper around HTML content with parsing capabilities."""

    def __init__(self, url: str, html: str, status_code: int = 200):
        self.url = url
        self.html = html
        self.status_code = status_code
        self._soup: Optional[BeautifulSoup] = None

    @property
    def soup(self) -> BeautifulSoup:
        """Lazy-load BeautifulSoup parser."""
        if self._soup is None:
            self._soup = BeautifulSoup(self.html, "lxml")
        return self._soup

    def select(self, selector: str) -> List[any]:
        """Select elements using CSS selector."""
        return self.soup.select(selector)

    def select_one(self, selector: str) -> Optional[any]:
        """Select first element matching CSS selector."""
        return self.soup.select_one(selector)


class HTMLFetcher(ABC):
    """Abstract base class for HTML fetchers."""

    def __init__(
        self,
        user_agents: Optional[List[str]] = None,
        timeout: int = 30,
    ):
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.timeout = timeout

    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the list."""
        return random.choice(self.user_agents)

    @abstractmethod
    async def fetch(self, url: str) -> HTMLDocument:
        """
        Fetch HTML content from a URL.

        Args:
            url: The URL to fetch

        Returns:
            HTMLDocument containing the page content

        Raises:
            Exception: If fetching fails
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass

    async def __aenter__(self) -> "HTMLFetcher":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


class RequestsFetcher(HTMLFetcher):
    """
    Fast HTML fetcher using httpx for static content.

    Best for:
    - Static HTML pages
    - APIs returning HTML
    - Sites without JavaScript rendering

    Not suitable for:
    - JavaScript-heavy SPAs
    - Pages with dynamic content loading
    - Sites requiring browser-like behavior
    """

    def __init__(
        self,
        user_agents: Optional[List[str]] = None,
        timeout: int = 30,
        follow_redirects: bool = True,
    ):
        super().__init__(user_agents, timeout)
        self.follow_redirects = follow_redirects
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-load HTTP client."""
        if self._client is None:
            # Create event hooks for redirect validation
            async def validate_redirect(response: httpx.Response):
                """Validate redirect URLs against SSRF attacks."""
                # Check if this is a redirect
                if 300 <= response.status_code < 400:
                    redirect_url = response.headers.get("location")
                    if redirect_url:
                        # Validate redirect URL
                        is_valid, error_msg = validate_url_ssrf(redirect_url)
                        if not is_valid:
                            raise httpx.HTTPError(
                                f"Blocked dangerous redirect to {redirect_url}: {error_msg}"
                            )

            event_hooks = {"response": [validate_redirect]} if self.follow_redirects else {}

            self._client = httpx.AsyncClient(
                follow_redirects=self.follow_redirects,
                timeout=self.timeout,
                event_hooks=event_hooks,
            )
        return self._client

    async def fetch(self, url: str) -> HTMLDocument:
        """
        Fetch HTML using HTTP request.

        Args:
            url: URL to fetch

        Returns:
            HTMLDocument with page content

        Raises:
            httpx.HTTPError: If request fails
        """
        headers = {
            "User-Agent": self._get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        response = await self.client.get(url, headers=headers)
        response.raise_for_status()

        return HTMLDocument(
            url=str(response.url),
            html=response.text,
            status_code=response.status_code,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None


class BrowserFetcher(HTMLFetcher):
    """
    Browser-based HTML fetcher using Playwright.

    Best for:
    - JavaScript-heavy sites
    - SPAs (Single Page Applications)
    - Sites with dynamic content
    - Infinite scroll
    - Sites that detect headless browsers

    Features:
    - Full browser automation
    - JavaScript execution
    - Network interception
    - Screenshots (future)
    """

    def __init__(
        self,
        user_agents: Optional[List[str]] = None,
        timeout: int = 30,
        headless: bool = True,
        wait_until: str = "networkidle",
    ):
        super().__init__(user_agents, timeout)
        self.headless = headless
        self.wait_until = wait_until  # "load", "domcontentloaded", "networkidle"
        self._playwright: Optional[PlaywrightContextManager] = None
        self._browser: Optional[Browser] = None

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is initialized."""
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
        return self._browser

    async def fetch(self, url: str) -> HTMLDocument:
        """
        Fetch HTML using browser automation.

        Args:
            url: URL to fetch

        Returns:
            HTMLDocument with page content (after JS execution)

        Raises:
            Exception: If browser navigation fails
        """
        browser = await self._ensure_browser()

        # Create new context with random user agent
        context = await browser.new_context(
            user_agent=self._get_random_user_agent(),
            viewport={"width": 1920, "height": 1080},
        )

        # Add stealth scripts to avoid detection
        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """
        )

        page = await context.new_page()

        try:
            # Navigate to page
            response = await page.goto(
                url, wait_until=self.wait_until, timeout=self.timeout * 1000
            )

            if response is None:
                raise Exception(f"Failed to load page: {url}")

            # Get HTML after JavaScript execution
            html = await page.content()
            status_code = response.status

            return HTMLDocument(url=page.url, html=html, status_code=status_code)

        finally:
            await context.close()

    async def scroll_to_bottom(
        self, page: Page, max_scrolls: int = 10, wait_ms: int = 1000
    ) -> None:
        """
        Scroll to bottom of page to trigger infinite scroll.

        Args:
            page: Playwright page instance
            max_scrolls: Maximum number of scrolls
            wait_ms: Wait time between scrolls
        """
        for _ in range(max_scrolls):
            # Get current scroll height
            previous_height = await page.evaluate("document.body.scrollHeight")

            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            # Wait for content to load
            await asyncio.sleep(wait_ms / 1000)

            # Check if new content loaded
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                break  # No more content to load

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None


class AutoFetcher(HTMLFetcher):
    """
    Smart fetcher that tries RequestsFetcher first, falls back to BrowserFetcher.

    Strategy:
    1. Try fast RequestsFetcher
    2. If page seems to need JS (very small content, known SPA indicators),
       retry with BrowserFetcher
    """

    def __init__(
        self,
        user_agents: Optional[List[str]] = None,
        timeout: int = 30,
    ):
        super().__init__(user_agents, timeout)
        self.requests_fetcher = RequestsFetcher(user_agents, timeout)
        self.browser_fetcher = BrowserFetcher(user_agents, timeout)

    def _needs_js_rendering(self, doc: HTMLDocument) -> bool:
        """
        Heuristic to determine if page needs JavaScript rendering.

        Checks:
        - Very small HTML (<500 chars often means SPA shell)
        - Common SPA root elements
        - Meta tags indicating SPA frameworks
        """
        if len(doc.html) < 500:
            return True

        soup = doc.soup

        # Check for common SPA indicators
        spa_indicators = [
            soup.find(id="root"),
            soup.find(id="app"),
            soup.find(attrs={"data-reactroot": True}),
            soup.find("div", id="__next"),  # Next.js
            soup.find("div", id="__nuxt"),  # Nuxt.js
        ]

        return any(indicator is not None for indicator in spa_indicators)

    async def fetch(self, url: str) -> HTMLDocument:
        """
        Fetch HTML, auto-detecting if browser is needed.

        Args:
            url: URL to fetch

        Returns:
            HTMLDocument with page content
        """
        # Try requests first (fast)
        try:
            doc = await self.requests_fetcher.fetch(url)

            # Check if we need browser
            if self._needs_js_rendering(doc):
                # Retry with browser
                return await self.browser_fetcher.fetch(url)

            return doc

        except Exception:
            # Fallback to browser on any error
            return await self.browser_fetcher.fetch(url)

    async def close(self) -> None:
        """Close both fetchers."""
        await self.requests_fetcher.close()
        await self.browser_fetcher.close()
