"""Tests for data models."""

import pytest
from pydantic import ValidationError

from grandma_scraper.core.models import (
    ScrapeJob,
    FieldConfig,
    PaginationStrategy,
    PaginationType,
    SelectorType,
    AttributeType,
    ScrapeResult,
    ScrapeStatus,
)


class TestFieldConfig:
    """Tests for FieldConfig model."""

    def test_basic_field_config(self):
        """Test creating a basic field config."""
        field = FieldConfig(
            name="title",
            selector=".title",
            attribute=AttributeType.TEXT,
        )

        assert field.name == "title"
        assert field.selector == ".title"
        assert field.selector_type == SelectorType.CSS
        assert field.attribute == AttributeType.TEXT
        assert field.multiple is False
        assert field.required is False

    def test_custom_attribute_requires_custom_attribute_name(self):
        """Test that CUSTOM attribute requires custom_attribute."""
        with pytest.raises(ValidationError):
            FieldConfig(
                name="data",
                selector=".data",
                attribute=AttributeType.CUSTOM,
                # Missing custom_attribute
            )

    def test_custom_attribute_with_name(self):
        """Test CUSTOM attribute with custom_attribute set."""
        field = FieldConfig(
            name="data",
            selector=".data",
            attribute=AttributeType.CUSTOM,
            custom_attribute="data-id",
        )

        assert field.custom_attribute == "data-id"


class TestPaginationStrategy:
    """Tests for PaginationStrategy model."""

    def test_no_pagination(self):
        """Test no pagination."""
        pagination = PaginationStrategy(type=PaginationType.NONE)
        assert pagination.type == PaginationType.NONE

    def test_next_button_requires_selector(self):
        """Test that NEXT_BUTTON requires selector."""
        with pytest.raises(ValidationError):
            PaginationStrategy(
                type=PaginationType.NEXT_BUTTON,
                # Missing next_button_selector
            )

    def test_next_button_with_selector(self):
        """Test NEXT_BUTTON with selector."""
        pagination = PaginationStrategy(
            type=PaginationType.NEXT_BUTTON,
            next_button_selector=".next > a",
        )

        assert pagination.next_button_selector == ".next > a"

    def test_url_pattern_requires_pattern(self):
        """Test that URL_PATTERN requires pattern."""
        with pytest.raises(ValidationError):
            PaginationStrategy(
                type=PaginationType.URL_PATTERN,
                # Missing url_pattern
            )

    def test_url_pattern_with_pattern(self):
        """Test URL_PATTERN with pattern."""
        pagination = PaginationStrategy(
            type=PaginationType.URL_PATTERN,
            url_pattern="?page={page}",
        )

        assert pagination.url_pattern == "?page={page}"


class TestScrapeJob:
    """Tests for ScrapeJob model."""

    def test_minimal_scrape_job(self):
        """Test creating minimal valid scrape job."""
        job = ScrapeJob(
            name="Test Job",
            start_url="https://example.com",
            item_selector=".item",
            fields=[
                FieldConfig(name="title", selector=".title"),
            ],
        )

        assert job.name == "Test Job"
        assert job.start_url == "https://example.com"
        assert len(job.fields) == 1
        assert job.enabled is True
        assert job.respect_robots_txt is True

    def test_url_must_have_scheme(self):
        """Test that URLs must start with http:// or https://."""
        with pytest.raises(ValidationError):
            ScrapeJob(
                name="Test",
                start_url="example.com",  # Missing scheme
                item_selector=".item",
                fields=[FieldConfig(name="title", selector=".title")],
            )

    def test_max_delay_must_be_gte_min_delay(self):
        """Test that max_delay >= min_delay."""
        with pytest.raises(ValidationError):
            ScrapeJob(
                name="Test",
                start_url="https://example.com",
                item_selector=".item",
                fields=[FieldConfig(name="title", selector=".title")],
                min_delay_ms=2000,
                max_delay_ms=1000,  # Less than min
            )

    def test_fields_cannot_be_empty(self):
        """Test that at least one field is required."""
        with pytest.raises(ValidationError):
            ScrapeJob(
                name="Test",
                start_url="https://example.com",
                item_selector=".item",
                fields=[],  # Empty
            )


class TestScrapeResult:
    """Tests for ScrapeResult model."""

    def test_initial_status(self):
        """Test initial result status."""
        from uuid import uuid4

        result = ScrapeResult(job_id=uuid4())

        assert result.status == ScrapeStatus.PENDING
        assert result.total_items == 0
        assert result.pages_scraped == 0
        assert result.started_at is None
        assert result.completed_at is None

    def test_mark_started(self):
        """Test marking result as started."""
        from uuid import uuid4

        result = ScrapeResult(job_id=uuid4())
        result.mark_started()

        assert result.status == ScrapeStatus.RUNNING
        assert result.started_at is not None

    def test_mark_completed(self):
        """Test marking result as completed."""
        from uuid import uuid4

        result = ScrapeResult(job_id=uuid4())
        result.items = [{"title": "Item 1"}, {"title": "Item 2"}]

        result.mark_started()
        result.mark_completed()

        assert result.status == ScrapeStatus.COMPLETED
        assert result.completed_at is not None
        assert result.total_items == 2
        assert result.duration_seconds is not None
        assert result.duration_seconds > 0

    def test_mark_failed(self):
        """Test marking result as failed."""
        from uuid import uuid4

        result = ScrapeResult(job_id=uuid4())
        result.mark_started()
        result.mark_failed("Test error", {"detail": "test"})

        assert result.status == ScrapeStatus.FAILED
        assert result.error_message == "Test error"
        assert result.error_details == {"detail": "test"}
        assert result.duration_seconds is not None

    def test_add_warning(self):
        """Test adding warnings."""
        from uuid import uuid4

        result = ScrapeResult(job_id=uuid4())
        result.add_warning("Warning 1")
        result.add_warning("Warning 2")

        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings
