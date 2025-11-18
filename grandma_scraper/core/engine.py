"""
Core scraping engine.

Orchestrates fetching, extraction, pagination, and result collection.
"""

import asyncio
import random
from typing import Optional, Callable, Any
from urllib.parse import urlparse, urljoin

from grandma_scraper.core.models import (
    ScrapeJob,
    ScrapeResult,
    ScrapeStatus,
    PaginationType,
    FetcherType,
)
from grandma_scraper.core.fetchers import (
    HTMLFetcher,
    RequestsFetcher,
    BrowserFetcher,
    AutoFetcher,
)
from grandma_scraper.core.extractors import DataExtractor, ExtractionError
from grandma_scraper.utils.robots import RobotsChecker
from grandma_scraper.utils.logger import get_logger


logger = get_logger(__name__)


class ScrapeEngine:
    """
    Main scraping engine.

    Responsibilities:
    - Fetch pages (respecting robots.txt)
    - Extract data using selectors
    - Handle pagination
    - Manage rate limiting and politeness
    - Collect and return results
    """

    def __init__(self, job: ScrapeJob):
        """
        Initialize scrape engine.

        Args:
            job: Scrape job configuration
        """
        self.job = job
        self.result = ScrapeResult(job_id=job.id)
        self.robots_checker = RobotsChecker(user_agent=job.user_agents[0])
        self._stop_requested = False

    async def run(
        self, progress_callback: Optional[Callable[[str, Any], None]] = None
    ) -> ScrapeResult:
        """
        Execute the scrape job.

        Args:
            progress_callback: Optional callback for progress updates
                              Called with (event_type, data)

        Returns:
            ScrapeResult with collected data
        """
        self.result.mark_started()
        self._emit_progress(progress_callback, "started", {"job_name": self.job.name})

        try:
            # Check robots.txt if required
            if self.job.respect_robots_txt:
                await self._check_robots_txt()

            # Choose fetcher based on job config
            fetcher = self._create_fetcher()

            async with fetcher:
                # Create extractor
                extractor = DataExtractor(
                    item_selector=self.job.item_selector,
                    fields=self.job.fields,
                    selector_type=self.job.item_selector_type,
                )

                # Scrape pages
                await self._scrape_pages(fetcher, extractor, progress_callback)

            # Mark as completed
            self.result.mark_completed()
            self._emit_progress(
                progress_callback,
                "completed",
                {
                    "total_items": self.result.total_items,
                    "pages_scraped": self.result.pages_scraped,
                    "duration": self.result.duration_seconds,
                },
            )

        except Exception as e:
            logger.error(f"Scrape job failed: {str(e)}", exc_info=True)
            self.result.mark_failed(str(e), {"exception_type": type(e).__name__})
            self._emit_progress(progress_callback, "failed", {"error": str(e)})

        return self.result

    async def _check_robots_txt(self) -> None:
        """Check if scraping is allowed by robots.txt."""
        allowed, reason = await self.robots_checker.can_fetch(self.job.start_url)

        if not allowed:
            warning = (
                f"robots.txt disallows scraping this URL: {self.job.start_url}. "
                f"Reason: {reason}. Proceeding anyway due to user override."
            )
            logger.warning(warning)
            self.result.add_warning(warning)

    def _create_fetcher(self) -> HTMLFetcher:
        """Create appropriate fetcher based on job configuration."""
        if self.job.fetcher_type == FetcherType.REQUESTS:
            return RequestsFetcher(
                user_agents=self.job.user_agents,
                timeout=self.job.timeout_seconds,
            )
        elif self.job.fetcher_type == FetcherType.BROWSER:
            return BrowserFetcher(
                user_agents=self.job.user_agents,
                timeout=self.job.timeout_seconds,
            )
        else:  # AUTO
            return AutoFetcher(
                user_agents=self.job.user_agents,
                timeout=self.job.timeout_seconds,
            )

    async def _scrape_pages(
        self,
        fetcher: HTMLFetcher,
        extractor: DataExtractor,
        progress_callback: Optional[Callable[[str, Any], None]],
    ) -> None:
        """
        Scrape all pages according to pagination strategy.

        Args:
            fetcher: HTML fetcher to use
            extractor: Data extractor
            progress_callback: Progress callback
        """
        urls_to_scrape = [self.job.start_url]
        page_num = 1

        while urls_to_scrape and not self._stop_requested:
            # Check limits
            if self.job.max_pages and page_num > self.job.max_pages:
                logger.info(f"Reached max pages limit: {self.job.max_pages}")
                break

            if self.job.max_items and self.result.total_items >= self.job.max_items:
                logger.info(f"Reached max items limit: {self.job.max_items}")
                break

            # Get next URL
            url = urls_to_scrape.pop(0)

            try:
                # Fetch page
                logger.info(f"Fetching page {page_num}: {url}")
                self._emit_progress(
                    progress_callback,
                    "fetching",
                    {"page": page_num, "url": url},
                )

                doc = await fetcher.fetch(url)

                # Extract data
                items = extractor.extract_from_document(doc)
                logger.info(f"Extracted {len(items)} items from page {page_num}")

                # Add to results (respecting max_items)
                if self.job.max_items:
                    remaining = self.job.max_items - self.result.total_items
                    items = items[:remaining]

                self.result.items.extend(items)
                self.result.total_items = len(self.result.items)
                self.result.pages_scraped = page_num

                self._emit_progress(
                    progress_callback,
                    "extracted",
                    {
                        "page": page_num,
                        "items_on_page": len(items),
                        "total_items": self.result.total_items,
                    },
                )

                # Handle pagination
                next_urls = await self._get_next_page_urls(doc, url, page_num)
                urls_to_scrape.extend(next_urls)

                page_num += 1

                # Polite delay before next request
                await self._polite_delay()

            except ExtractionError as e:
                logger.error(f"Extraction failed for {url}: {str(e)}")
                self.result.add_warning(f"Extraction failed for page {page_num}: {str(e)}")

            except Exception as e:
                logger.error(f"Failed to scrape {url}: {str(e)}")
                self.result.add_warning(f"Failed to scrape page {page_num}: {str(e)}")

    async def _get_next_page_urls(self, doc, current_url: str, page_num: int) -> list[str]:
        """
        Get URLs for next pages based on pagination strategy.

        Args:
            doc: Current page HTML document
            current_url: Current page URL
            page_num: Current page number

        Returns:
            List of URLs to scrape next
        """
        pagination = self.job.pagination

        if pagination.type == PaginationType.NONE:
            return []

        elif pagination.type == PaginationType.URL_PATTERN:
            # Generate next URL from pattern
            if pagination.url_pattern:
                next_page_num = page_num + 1
                parsed = urlparse(current_url)

                # Simple pattern substitution
                if "{page}" in pagination.url_pattern:
                    next_url_part = pagination.url_pattern.format(page=next_page_num)

                    # Append or replace query string
                    if "?" in current_url:
                        # Replace existing page param or append
                        base_url = current_url.split("?")[0]
                        next_url = f"{base_url}{next_url_part}"
                    else:
                        next_url = f"{current_url}{next_url_part}"

                    return [next_url]

        elif pagination.type == PaginationType.NEXT_BUTTON:
            # Find "Next" button and extract href
            if pagination.next_button_selector:
                try:
                    next_link = doc.select_one(pagination.next_button_selector)
                    if next_link and next_link.get("href"):
                        href = next_link.get("href")
                        # Make absolute URL
                        next_url = urljoin(current_url, href)
                        return [next_url]
                except Exception as e:
                    logger.warning(f"Failed to find next button: {str(e)}")

        # INFINITE_SCROLL is handled differently (in BrowserFetcher)
        # and would require special logic

        return []

    async def _polite_delay(self) -> None:
        """Wait a random time between min and max delay."""
        delay_ms = random.uniform(self.job.min_delay_ms, self.job.max_delay_ms)
        await asyncio.sleep(delay_ms / 1000)

    def _emit_progress(
        self,
        callback: Optional[Callable[[str, Any], None]],
        event_type: str,
        data: Any,
    ) -> None:
        """Emit progress event if callback is provided."""
        if callback:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.warning(f"Progress callback error: {str(e)}")

    def stop(self) -> None:
        """Request the scraper to stop gracefully."""
        self._stop_requested = True
        logger.info("Stop requested")
