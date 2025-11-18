"""Tests for data extraction."""

from pathlib import Path

import pytest

from grandma_scraper.core.models import FieldConfig, SelectorType, AttributeType
from grandma_scraper.core.extractors import DataExtractor
from grandma_scraper.core.fetchers import HTMLDocument


@pytest.fixture
def sample_html():
    """Load sample HTML fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample.html"
    return fixture_path.read_text()


@pytest.fixture
def sample_document(sample_html):
    """Create HTMLDocument from sample HTML."""
    return HTMLDocument(url="http://example.com", html=sample_html)


class TestDataExtractor:
    """Tests for DataExtractor."""

    def test_extract_basic_fields(self, sample_document):
        """Test extracting basic text fields."""
        fields = [
            FieldConfig(name="title", selector=".title", attribute=AttributeType.TEXT),
            FieldConfig(name="price", selector=".price", attribute=AttributeType.TEXT),
        ]

        extractor = DataExtractor(
            item_selector=".product",
            fields=fields,
            selector_type=SelectorType.CSS,
        )

        results = extractor.extract_from_document(sample_document)

        assert len(results) == 3
        assert results[0]["title"] == "Laptop Pro 2024"
        assert results[0]["price"] == "$1,299.99"
        assert results[1]["title"] == "Wireless Mouse"
        assert results[2]["title"] == "USB-C Cable"

    def test_extract_href_attribute(self, sample_document):
        """Test extracting href attributes."""
        fields = [
            FieldConfig(name="title", selector=".title"),
            FieldConfig(name="url", selector=".link", attribute=AttributeType.HREF),
        ]

        extractor = DataExtractor(
            item_selector=".product",
            fields=fields,
            selector_type=SelectorType.CSS,
        )

        results = extractor.extract_from_document(sample_document)

        assert results[0]["url"] == "/products/laptop-pro"
        assert results[1]["url"] == "/products/wireless-mouse"

    def test_extract_multiple_values(self, sample_document):
        """Test extracting multiple values (list)."""
        fields = [
            FieldConfig(name="title", selector=".title"),
            FieldConfig(
                name="categories",
                selector=".category",
                multiple=True,
            ),
        ]

        extractor = DataExtractor(
            item_selector=".product",
            fields=fields,
            selector_type=SelectorType.CSS,
        )

        results = extractor.extract_from_document(sample_document)

        # First product has 2 categories
        assert results[0]["categories"] == ["Electronics", "Computers"]
        # Second product has 2 categories
        assert results[1]["categories"] == ["Electronics", "Accessories"]
        # Third product has 1 category
        assert results[2]["categories"] == ["Accessories"]

    def test_required_field_skips_item(self, sample_document):
        """Test that missing required field skips the item."""
        fields = [
            FieldConfig(name="title", selector=".title"),
            FieldConfig(
                name="missing",
                selector=".does-not-exist",
                required=True,
            ),
        ]

        extractor = DataExtractor(
            item_selector=".product",
            fields=fields,
            selector_type=SelectorType.CSS,
        )

        results = extractor.extract_from_document(sample_document)

        # All items should be skipped due to missing required field
        assert len(results) == 0

    def test_default_value(self, sample_document):
        """Test default values for missing fields."""
        fields = [
            FieldConfig(name="title", selector=".title"),
            FieldConfig(
                name="missing",
                selector=".does-not-exist",
                default_value="N/A",
            ),
        ]

        extractor = DataExtractor(
            item_selector=".product",
            fields=fields,
            selector_type=SelectorType.CSS,
        )

        results = extractor.extract_from_document(sample_document)

        assert len(results) == 3
        for result in results:
            assert result["missing"] == "N/A"

    def test_validate_selectors(self, sample_document):
        """Test selector validation."""
        fields = [
            FieldConfig(name="title", selector=".title"),
            FieldConfig(name="price", selector=".price"),
            FieldConfig(name="missing", selector=".does-not-exist"),
        ]

        extractor = DataExtractor(
            item_selector=".product",
            fields=fields,
            selector_type=SelectorType.CSS,
        )

        validation = extractor.validate_selectors(sample_document)

        assert validation["items_found"] == 3
        assert validation["fields"]["title"]["found"] is True
        assert validation["fields"]["title"]["sample_value"] == "Laptop Pro 2024"
        assert validation["fields"]["price"]["found"] is True
        assert validation["fields"]["missing"]["found"] is False

    def test_no_items_found(self, sample_document):
        """Test when item selector matches nothing."""
        fields = [FieldConfig(name="title", selector=".title")]

        extractor = DataExtractor(
            item_selector=".does-not-exist",
            fields=fields,
            selector_type=SelectorType.CSS,
        )

        results = extractor.extract_from_document(sample_document)

        assert len(results) == 0
