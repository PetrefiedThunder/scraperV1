"""
Main CLI entry point for GrandmaScraper.

Provides commands for running, validating, and managing scrape jobs.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from grandma_scraper import __version__
from grandma_scraper.core.models import ScrapeJob
from grandma_scraper.core.engine import ScrapeEngine
from grandma_scraper.core.exporters import DataExporter
from grandma_scraper.utils.logger import setup_logger, get_logger


app = typer.Typer(
    name="grandma-scraper",
    help="A grandma-friendly, production-grade web scraping tool 🕷️",
    add_completion=False,
)
console = Console()
logger = get_logger()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"GrandmaScraper version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose logging",
    ),
) -> None:
    """GrandmaScraper - Powerful yet simple web scraping."""
    # Set up logging
    import logging

    level = logging.DEBUG if verbose else logging.INFO
    setup_logger(level=level)


@app.command()
def run(
    config: Path = typer.Argument(
        ...,
        help="Path to scrape job config file (YAML or JSON)",
        exists=True,
        dir_okay=False,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (format auto-detected from extension)",
    ),
    export_format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Export format: csv, json, or excel",
    ),
) -> None:
    """
    Run a scrape job from a configuration file.

    Example:
        grandma-scraper run config/my-scraper.yaml -o output/results.csv
    """
    try:
        # Load config
        console.print(f"[cyan]Loading config from:[/cyan] {config}")
        job = load_job_from_file(config)

        console.print(f"[green]✓[/green] Loaded job: [bold]{job.name}[/bold]")
        console.print(f"  Start URL: {job.start_url}")
        console.print(f"  Fields: {', '.join(f.name for f in job.fields)}")

        # Show ethical disclaimer
        if not job.respect_robots_txt:
            console.print(
                "\n[yellow]⚠ Warning:[/yellow] robots.txt checking is DISABLED.\n"
                "  Please ensure you have permission to scrape this website.\n"
            )

        # Run scrape
        console.print("\n[cyan]Starting scrape...[/cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scraping...", total=None)

            def update_progress(event_type: str, data: dict) -> None:
                if event_type == "fetching":
                    progress.update(
                        task, description=f"Fetching page {data['page']}..."
                    )
                elif event_type == "extracted":
                    progress.update(
                        task,
                        description=f"Extracted {data['total_items']} items from {data['page']} pages...",
                    )

            result = asyncio.run(run_scrape_job(job, update_progress))

        # Show results
        console.print()
        if result.status.value == "completed":
            console.print("[green]✓ Scrape completed successfully![/green]")
            console.print(f"  Items collected: {result.total_items}")
            console.print(f"  Pages scraped: {result.pages_scraped}")
            console.print(
                f"  Duration: {result.duration_seconds:.2f}s"
                if result.duration_seconds
                else ""
            )

            # Show warnings
            if result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  • {warning}")

            # Export if output specified
            if output and result.items:
                console.print(f"\n[cyan]Exporting to:[/cyan] {output}")
                DataExporter.export(result.items, str(output), export_format)
                console.print("[green]✓ Export complete![/green]")
            elif result.items:
                # Show sample data
                console.print("\n[cyan]Sample data (first 5 items):[/cyan]")
                show_data_table(result.items[:5])

                console.print(
                    "\n[dim]Tip: Use --output to save results to a file[/dim]"
                )
            else:
                console.print("\n[yellow]No items were collected[/yellow]")

        else:
            console.print(f"[red]✗ Scrape failed:[/red] {result.error_message}")
            if result.error_details:
                console.print(f"  Details: {result.error_details}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        logger.exception("Command failed")
        sys.exit(1)


@app.command()
def validate(
    config: Path = typer.Argument(
        ...,
        help="Path to scrape job config file to validate",
        exists=True,
        dir_okay=False,
    ),
) -> None:
    """
    Validate a scrape job configuration file.

    Checks:
    - YAML/JSON syntax
    - Required fields
    - Field types and constraints
    - Selector syntax
    """
    try:
        console.print(f"[cyan]Validating config:[/cyan] {config}")

        # Try to load job
        job = load_job_from_file(config)

        # Validation passed
        console.print("[green]✓ Configuration is valid![/green]\n")

        # Show summary
        console.print(f"[bold]Job:[/bold] {job.name}")
        if job.description:
            console.print(f"[dim]{job.description}[/dim]")

        console.print(f"\n[bold]Target:[/bold] {job.start_url}")

        console.print(f"\n[bold]Fields ({len(job.fields)}):[/bold]")
        for field in job.fields:
            required = "[red]*[/red]" if field.required else ""
            console.print(f"  • {field.name}{required}: {field.selector}")

        console.print(f"\n[bold]Pagination:[/bold] {job.pagination.type.value}")

        if job.max_pages:
            console.print(f"[bold]Max pages:[/bold] {job.max_pages}")
        if job.max_items:
            console.print(f"[bold]Max items:[/bold] {job.max_items}")

    except Exception as e:
        console.print(f"[red]✗ Validation failed:[/red]\n")
        console.print(f"  {str(e)}")
        sys.exit(1)


@app.command()
def init(
    name: str = typer.Argument(..., help="Name for the scrape job"),
    url: str = typer.Argument(..., help="Starting URL to scrape"),
    output: Path = typer.Option(
        "config/scraper.yaml",
        "--output",
        "-o",
        help="Output config file path",
    ),
) -> None:
    """
    Initialize a new scrape job configuration file.

    Creates a template config that you can customize.

    Example:
        grandma-scraper init "My News Scraper" "https://news.example.com"
    """
    try:
        # Create template job
        job = ScrapeJob(
            name=name,
            description=f"Scrape job for {url}",
            start_url=url,
            item_selector=".item",  # Placeholder
            fields=[
                {
                    "name": "title",
                    "selector": "h2",
                    "selector_type": "css",
                    "attribute": "text",
                },
                {
                    "name": "link",
                    "selector": "a",
                    "selector_type": "css",
                    "attribute": "href",
                },
            ],
        )

        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)

        # Export to YAML
        with open(output, "w") as f:
            # Convert to dict (exclude defaults)
            data = job.model_dump(mode="json", exclude_none=True)
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]✓ Created config file:[/green] {output}")
        console.print("\n[yellow]Next steps:[/yellow]")
        console.print(f"  1. Edit {output} to customize selectors")
        console.print(f"  2. Run: grandma-scraper validate {output}")
        console.print(f"  3. Run: grandma-scraper run {output} -o results.csv")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


def load_job_from_file(file_path: Path) -> ScrapeJob:
    """Load a ScrapeJob from YAML or JSON file."""
    suffix = file_path.suffix.lower()

    with open(file_path, "r") as f:
        if suffix in (".yaml", ".yml"):
            data = yaml.safe_load(f)
        elif suffix == ".json":
            import json

            data = json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {suffix}")

    return ScrapeJob(**data)


async def run_scrape_job(job: ScrapeJob, progress_callback=None):
    """Run a scrape job asynchronously."""
    engine = ScrapeEngine(job)
    return await engine.run(progress_callback)


def show_data_table(items: list) -> None:
    """Display data items as a rich table."""
    if not items:
        return

    # Get all keys
    keys = set()
    for item in items:
        keys.update(item.keys())
    keys = sorted(keys)

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    for key in keys:
        table.add_column(key, overflow="fold", max_width=40)

    # Add rows
    for item in items:
        row = [str(item.get(key, "")) for key in keys]
        table.add_row(*row)

    console.print(table)


if __name__ == "__main__":
    app()
