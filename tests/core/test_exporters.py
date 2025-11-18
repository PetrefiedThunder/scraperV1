"""Tests for data exporters."""

import csv
import json
from pathlib import Path

import pytest
import pandas as pd

from grandma_scraper.core.exporters import DataExporter, ExportError


@pytest.fixture
def sample_data():
    """Sample scraped data."""
    return [
        {"title": "Product 1", "price": "$10.00", "rating": 4.5},
        {"title": "Product 2", "price": "$20.00", "rating": 5.0},
        {"title": "Product 3", "price": "$15.00", "rating": 4.0},
    ]


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test outputs."""
    return tmp_path


class TestCSVExport:
    """Tests for CSV export."""

    def test_export_csv(self, sample_data, temp_dir):
        """Test basic CSV export."""
        output_file = temp_dir / "test.csv"

        DataExporter.export_csv(sample_data, str(output_file))

        assert output_file.exists()

        # Read and verify
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["title"] == "Product 1"
        assert rows[0]["price"] == "$10.00"

    def test_export_csv_empty_data(self, temp_dir):
        """Test exporting empty data."""
        output_file = temp_dir / "empty.csv"

        DataExporter.export_csv([], str(output_file))

        assert output_file.exists()

    def test_export_csv_creates_directories(self, temp_dir):
        """Test that export creates parent directories."""
        output_file = temp_dir / "nested" / "dir" / "test.csv"

        DataExporter.export_csv([{"a": "b"}], str(output_file))

        assert output_file.exists()


class TestJSONExport:
    """Tests for JSON export."""

    def test_export_json(self, sample_data, temp_dir):
        """Test basic JSON export."""
        output_file = temp_dir / "test.json"

        DataExporter.export_json(sample_data, str(output_file))

        assert output_file.exists()

        # Read and verify
        with open(output_file, "r") as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]["title"] == "Product 1"
        assert data[0]["rating"] == 4.5

    def test_export_json_compact(self, sample_data, temp_dir):
        """Test compact JSON export."""
        output_file = temp_dir / "compact.json"

        DataExporter.export_json(sample_data, str(output_file), indent=None)

        assert output_file.exists()

        # Should be more compact
        content = output_file.read_text()
        assert "\n" not in content or content.count("\n") < 10


class TestExcelExport:
    """Tests for Excel export."""

    def test_export_excel(self, sample_data, temp_dir):
        """Test basic Excel export."""
        output_file = temp_dir / "test.xlsx"

        DataExporter.export_excel(sample_data, str(output_file))

        assert output_file.exists()

        # Read and verify
        df = pd.read_excel(output_file, engine="openpyxl")

        assert len(df) == 3
        assert df.iloc[0]["title"] == "Product 1"
        assert df.iloc[0]["price"] == "$10.00"

    def test_export_excel_empty_data(self, temp_dir):
        """Test exporting empty data to Excel."""
        output_file = temp_dir / "empty.xlsx"

        DataExporter.export_excel([], str(output_file))

        assert output_file.exists()


class TestAutoExport:
    """Tests for automatic format detection."""

    def test_auto_detect_csv(self, sample_data, temp_dir):
        """Test auto-detecting CSV format."""
        output_file = temp_dir / "test.csv"

        DataExporter.export(sample_data, str(output_file))

        assert output_file.exists()

        # Verify it's CSV
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3

    def test_auto_detect_json(self, sample_data, temp_dir):
        """Test auto-detecting JSON format."""
        output_file = temp_dir / "test.json"

        DataExporter.export(sample_data, str(output_file))

        assert output_file.exists()

        with open(output_file, "r") as f:
            data = json.load(f)

        assert len(data) == 3

    def test_auto_detect_excel(self, sample_data, temp_dir):
        """Test auto-detecting Excel format."""
        output_file = temp_dir / "test.xlsx"

        DataExporter.export(sample_data, str(output_file))

        assert output_file.exists()

        df = pd.read_excel(output_file, engine="openpyxl")
        assert len(df) == 3

    def test_unsupported_format_raises_error(self, sample_data, temp_dir):
        """Test that unsupported format raises error."""
        output_file = temp_dir / "test.txt"

        with pytest.raises(ExportError):
            DataExporter.export(sample_data, str(output_file))

    def test_format_override(self, sample_data, temp_dir):
        """Test overriding format detection."""
        output_file = temp_dir / "test.dat"

        # Override to CSV
        DataExporter.export(sample_data, str(output_file), format="csv")

        assert output_file.exists()

        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
