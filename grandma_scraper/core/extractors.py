"""
Data extraction from HTML using CSS selectors and XPath.

Handles structured data extraction based on field configurations.
"""

from typing import Any, Dict, List, Optional
from lxml import etree, html as lxml_html

from grandma_scraper.core.models import (
    FieldConfig,
    SelectorType,
    AttributeType,
)
from grandma_scraper.core.fetchers import HTMLDocument


class ExtractionError(Exception):
    """Raised when data extraction fails."""

    pass


class DataExtractor:
    """
    Extracts structured data from HTML documents.

    Supports:
    - CSS selectors and XPath
    - Multiple attribute types (text, href, src, custom)
    - Required vs optional fields
    - Default values
    """

    def __init__(self, item_selector: str, fields: List[FieldConfig], selector_type: SelectorType):
        """
        Initialize extractor.

        Args:
            item_selector: Selector for container elements
            fields: List of field configurations
            selector_type: Type of item selector (CSS or XPath)
        """
        self.item_selector = item_selector
        self.fields = fields
        self.selector_type = selector_type

    def extract_from_document(self, doc: HTMLDocument) -> List[Dict[str, Any]]:
        """
        Extract all items from a document.

        Args:
            doc: HTML document to extract from

        Returns:
            List of extracted records (dicts)

        Raises:
            ExtractionError: If extraction fails
        """
        try:
            # Parse HTML with lxml for XPath support
            tree = lxml_html.fromstring(doc.html)

            # Find all item containers
            if self.selector_type == SelectorType.CSS:
                items = tree.cssselect(self.item_selector)
            else:
                items = tree.xpath(self.item_selector)

            if not items:
                return []

            # Extract fields from each item
            results = []
            for item in items:
                record = self._extract_item(item)
                if record is not None:
                    results.append(record)

            return results

        except Exception as e:
            raise ExtractionError(f"Failed to extract data: {str(e)}") from e

    def _extract_item(self, element: etree.Element) -> Optional[Dict[str, Any]]:
        """
        Extract fields from a single item element.

        Args:
            element: HTML element representing one item

        Returns:
            Dictionary of field values, or None if required fields missing
        """
        record: Dict[str, Any] = {}

        for field in self.fields:
            try:
                value = self._extract_field(element, field)

                # Handle required fields
                if value is None and field.required:
                    return None  # Skip this item

                # Use default value if provided
                if value is None and field.default_value is not None:
                    value = field.default_value

                record[field.name] = value

            except Exception as e:
                # If field is required, skip the entire item
                if field.required:
                    return None
                # Otherwise, use default or None
                record[field.name] = field.default_value

        return record

    def _extract_field(self, element: etree.Element, field: FieldConfig) -> Any:
        """
        Extract a single field value.

        Args:
            element: Parent element to search within
            field: Field configuration

        Returns:
            Extracted value(s) - string, list of strings, or None
        """
        # Find target elements
        if field.selector_type == SelectorType.CSS:
            targets = element.cssselect(field.selector)
        else:
            targets = element.xpath(field.selector)

        if not targets:
            return None

        # Extract values
        if field.multiple:
            # Extract from all matches
            values = [self._get_value_from_element(t, field) for t in targets]
            return [v for v in values if v is not None]  # Filter out None
        else:
            # Extract from first match
            return self._get_value_from_element(targets[0], field)

    def _get_value_from_element(self, element: etree.Element, field: FieldConfig) -> Optional[str]:
        """
        Get value from element based on attribute type.

        Args:
            element: HTML element
            field: Field configuration

        Returns:
            Extracted string value or None
        """
        if field.attribute == AttributeType.TEXT:
            # Get text content
            text = element.text_content().strip()
            return text if text else None

        elif field.attribute == AttributeType.HTML:
            # Get inner HTML
            return etree.tostring(element, encoding="unicode", method="html")

        elif field.attribute == AttributeType.HREF:
            return element.get("href")

        elif field.attribute == AttributeType.SRC:
            return element.get("src")

        elif field.attribute == AttributeType.VALUE:
            return element.get("value")

        elif field.attribute == AttributeType.CUSTOM:
            if field.custom_attribute:
                return element.get(field.custom_attribute)
            return None

        return None

    def validate_selectors(self, doc: HTMLDocument) -> Dict[str, Any]:
        """
        Validate that selectors work on a sample document.

        Args:
            doc: Sample HTML document

        Returns:
            Dict with validation results:
            {
                "items_found": int,
                "fields": {
                    "field_name": {
                        "found": bool,
                        "sample_value": str or None
                    }
                }
            }
        """
        tree = lxml_html.fromstring(doc.html)

        # Check item selector
        if self.selector_type == SelectorType.CSS:
            items = tree.cssselect(self.item_selector)
        else:
            items = tree.xpath(self.item_selector)

        result = {
            "items_found": len(items),
            "fields": {},
        }

        if items:
            # Test field selectors on first item
            first_item = items[0]
            for field in self.fields:
                try:
                    value = self._extract_field(first_item, field)
                    result["fields"][field.name] = {
                        "found": value is not None,
                        "sample_value": value,
                    }
                except Exception as e:
                    result["fields"][field.name] = {
                        "found": False,
                        "error": str(e),
                    }

        return result
