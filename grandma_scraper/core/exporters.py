"""
Data export functionality.

Supports exporting scraped data to various formats:
- CSV
- JSON
- Excel (.xlsx)
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from grandma_scraper.utils.logger import get_logger


logger = get_logger(__name__)


class ExportError(Exception):
    """Raised when export fails."""

    pass


class DataExporter:
    """
    Export scraped data to various formats.

    Supports:
    - CSV: Simple, universal format
    - JSON: Structured, preserves types
    - Excel: User-friendly for non-technical users
    """

    @staticmethod
    def export_csv(records: List[Dict[str, Any]], file_path: str) -> None:
        """
        Export records to CSV file.

        Args:
            records: List of dictionaries to export
            file_path: Output file path

        Raises:
            ExportError: If export fails
        """
        try:
            if not records:
                logger.warning("No records to export")
                # Create empty file
                Path(file_path).touch()
                return

            # Ensure parent directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Get all unique keys across all records
            fieldnames = set()
            for record in records:
                fieldnames.update(record.keys())
            fieldnames = sorted(fieldnames)

            # Write CSV
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)

            logger.info(f"Exported {len(records)} records to CSV: {file_path}")

        except Exception as e:
            raise ExportError(f"Failed to export to CSV: {str(e)}") from e

    @staticmethod
    def export_json(
        records: List[Dict[str, Any]], file_path: str, indent: int = 2
    ) -> None:
        """
        Export records to JSON file.

        Args:
            records: List of dictionaries to export
            file_path: Output file path
            indent: JSON indentation (None for compact)

        Raises:
            ExportError: If export fails
        """
        try:
            # Ensure parent directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Write JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=indent, ensure_ascii=False, default=str)

            logger.info(f"Exported {len(records)} records to JSON: {file_path}")

        except Exception as e:
            raise ExportError(f"Failed to export to JSON: {str(e)}") from e

    @staticmethod
    def export_excel(records: List[Dict[str, Any]], file_path: str) -> None:
        """
        Export records to Excel file (.xlsx).

        Args:
            records: List of dictionaries to export
            file_path: Output file path

        Raises:
            ExportError: If export fails
        """
        try:
            if not records:
                logger.warning("No records to export")
                # Create empty Excel file
                df = pd.DataFrame()
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                df.to_excel(file_path, index=False, engine="openpyxl")
                return

            # Ensure parent directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Convert to DataFrame
            df = pd.DataFrame(records)

            # Write Excel with basic formatting
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Scraped Data")

                # Auto-adjust column widths
                worksheet = writer.sheets["Scraped Data"]
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(), len(str(col))
                    )
                    # Add some padding
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[
                        chr(65 + idx)
                    ].width = adjusted_width

            logger.info(f"Exported {len(records)} records to Excel: {file_path}")

        except Exception as e:
            raise ExportError(f"Failed to export to Excel: {str(e)}") from e

    @staticmethod
    def export(
        records: List[Dict[str, Any]], file_path: str, format: str = None
    ) -> None:
        """
        Export records to file, auto-detecting format from extension.

        Args:
            records: List of dictionaries to export
            file_path: Output file path
            format: Format override ("csv", "json", "excel")

        Raises:
            ExportError: If format is unsupported or export fails
        """
        # Determine format
        if format is None:
            # Auto-detect from extension
            suffix = Path(file_path).suffix.lower()
            format_map = {
                ".csv": "csv",
                ".json": "json",
                ".xlsx": "excel",
                ".xls": "excel",
            }
            format = format_map.get(suffix)

            if format is None:
                raise ExportError(
                    f"Cannot determine format from extension: {suffix}. "
                    f"Supported: .csv, .json, .xlsx"
                )

        # Export using appropriate method
        if format == "csv":
            DataExporter.export_csv(records, file_path)
        elif format == "json":
            DataExporter.export_json(records, file_path)
        elif format in ("excel", "xlsx"):
            DataExporter.export_excel(records, file_path)
        else:
            raise ExportError(
                f"Unsupported export format: {format}. "
                f"Supported: csv, json, excel"
            )
