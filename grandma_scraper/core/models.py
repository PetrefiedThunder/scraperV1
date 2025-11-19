"""
Core data models for scrape jobs and results.

These models define the structure of scraping configurations, results, and related data.
All models use Pydantic for validation and serialization.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class SelectorType(str, Enum):
    """Type of selector to use for element extraction."""

    CSS = "css"
    XPATH = "xpath"


class AttributeType(str, Enum):
    """Which attribute to extract from matched elements."""

    TEXT = "text"  # innerText
    HTML = "html"  # innerHTML
    HREF = "href"
    SRC = "src"
    VALUE = "value"
    CUSTOM = "custom"  # User-specified attribute


class FieldConfig(BaseModel):
    """Configuration for a single field to extract."""

    name: str = Field(..., description="Field name (e.g., 'title', 'price')")
    selector: str = Field(..., description="CSS selector or XPath expression")
    selector_type: SelectorType = Field(
        default=SelectorType.CSS, description="Type of selector"
    )
    attribute: AttributeType = Field(
        default=AttributeType.TEXT, description="Which attribute to extract"
    )
    custom_attribute: Optional[str] = Field(
        default=None, description="Custom attribute name if attribute=CUSTOM"
    )
    multiple: bool = Field(
        default=False,
        description="Extract multiple values (returns list) or just first match",
    )
    required: bool = Field(
        default=False, description="Whether this field must be present in results"
    )
    default_value: Optional[str] = Field(
        default=None, description="Default value if field not found"
    )

    @model_validator(mode="after")
    def validate_custom_attribute(self) -> "FieldConfig":
        """Ensure custom_attribute is set when attribute=CUSTOM."""
        if self.attribute == AttributeType.CUSTOM and not self.custom_attribute:
            raise ValueError("custom_attribute must be set when attribute=CUSTOM")
        return self


class PaginationType(str, Enum):
    """Strategy for handling pagination."""

    NONE = "none"
    NEXT_BUTTON = "next_button"  # Click "Next" button
    URL_PATTERN = "url_pattern"  # Increment page number in URL
    INFINITE_SCROLL = "infinite_scroll"  # Scroll to load more


class PaginationStrategy(BaseModel):
    """Configuration for pagination handling."""

    type: PaginationType = Field(
        default=PaginationType.NONE, description="Pagination strategy to use"
    )
    next_button_selector: Optional[str] = Field(
        default=None, description="Selector for 'Next' button (for NEXT_BUTTON type)"
    )
    url_pattern: Optional[str] = Field(
        default=None,
        description="URL pattern with {page} placeholder (e.g., '?page={page}')",
    )
    max_scrolls: Optional[int] = Field(
        default=10, description="Max scrolls for INFINITE_SCROLL type"
    )
    scroll_wait_ms: int = Field(
        default=1000, description="Wait time after scroll (milliseconds)"
    )

    @model_validator(mode="after")
    def validate_pagination_config(self) -> "PaginationStrategy":
        """Validate pagination configuration based on type."""
        if self.type == PaginationType.NEXT_BUTTON and not self.next_button_selector:
            raise ValueError("next_button_selector required for NEXT_BUTTON pagination")
        if self.type == PaginationType.URL_PATTERN and not self.url_pattern:
            raise ValueError("url_pattern required for URL_PATTERN pagination")
        return self


class FetcherType(str, Enum):
    """Type of HTML fetcher to use."""

    AUTO = "auto"  # Auto-detect (try requests first, fallback to browser)
    REQUESTS = "requests"  # Fast, static HTML only
    BROWSER = "browser"  # Slower, handles JavaScript


class ScrapeJob(BaseModel):
    """Complete configuration for a scraping job."""

    # Identity
    id: UUID = Field(default_factory=uuid4, description="Unique job identifier")
    name: str = Field(..., description="Human-readable job name")
    description: Optional[str] = Field(
        default=None, description="Job description for documentation"
    )
    enabled: bool = Field(default=True, description="Whether this job is active")

    # Target
    start_url: str = Field(..., description="Starting URL for scraping")

    # Selectors
    item_selector: str = Field(
        ...,
        description="Selector for container elements (each match = one record)",
    )
    item_selector_type: SelectorType = Field(
        default=SelectorType.CSS, description="Type of item selector"
    )
    fields: List[FieldConfig] = Field(
        ..., min_length=1, description="Fields to extract from each item"
    )

    # Pagination
    pagination: PaginationStrategy = Field(
        default_factory=PaginationStrategy, description="Pagination configuration"
    )

    # Limits
    max_pages: Optional[int] = Field(
        default=None, description="Maximum pages to scrape (None = unlimited)", ge=1, le=10000
    )
    max_items: Optional[int] = Field(
        default=None, description="Maximum items to collect (None = unlimited)", ge=1, le=1000000
    )
    timeout_seconds: int = Field(
        default=30, description="Timeout for each page request", ge=1, le=300
    )
    retry_count: int = Field(default=3, description="Number of retries on failure", ge=0, le=10)

    # Politeness & Anti-bot
    fetcher_type: FetcherType = Field(
        default=FetcherType.AUTO, description="Which fetcher to use"
    )
    min_delay_ms: int = Field(
        default=1000, description="Minimum delay between requests (ms)", ge=0
    )
    max_delay_ms: int = Field(
        default=3000, description="Maximum delay between requests (ms)", ge=0
    )
    concurrent_requests: int = Field(
        default=1, description="Number of concurrent requests", ge=1, le=10
    )
    user_agents: List[str] = Field(
        default_factory=lambda: [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        description="List of user agents to rotate through",
    )
    respect_robots_txt: bool = Field(
        default=True, description="Whether to check and respect robots.txt"
    )

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("start_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL has a scheme and is safe from SSRF attacks."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        # Import here to avoid circular dependency
        from grandma_scraper.utils.url_validator import validate_url_ssrf_strict, SSRFProtectionError

        try:
            validate_url_ssrf_strict(v)
        except SSRFProtectionError as e:
            raise ValueError(f"Unsafe URL blocked by SSRF protection: {str(e)}")

        return v

    @model_validator(mode="after")
    def validate_delays(self) -> "ScrapeJob":
        """Ensure max_delay >= min_delay."""
        if self.max_delay_ms < self.min_delay_ms:
            raise ValueError("max_delay_ms must be >= min_delay_ms")
        return self


class ScrapeStatus(str, Enum):
    """Status of a scrape job execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeResult(BaseModel):
    """Results and metadata from a scrape job execution."""

    job_id: UUID = Field(..., description="ID of the job that was executed")
    run_id: UUID = Field(default_factory=uuid4, description="Unique ID for this run")
    status: ScrapeStatus = Field(default=ScrapeStatus.PENDING)

    # Results
    items: List[Dict[str, Any]] = Field(
        default_factory=list, description="Scraped data items"
    )
    total_items: int = Field(default=0, description="Total items collected")
    pages_scraped: int = Field(default=0, description="Number of pages processed")

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Errors
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    # Warnings
    warnings: List[str] = Field(default_factory=list)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def mark_started(self) -> None:
        """Mark the scrape as started."""
        self.status = ScrapeStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        """Mark the scrape as completed successfully."""
        self.status = ScrapeStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.total_items = len(self.items)

    def mark_failed(self, error: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Mark the scrape as failed."""
        self.status = ScrapeStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.error_message = error
        self.error_details = details
