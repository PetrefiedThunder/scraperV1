# Developer Guide

This guide is for developers who want to contribute to GrandmaScraper or extend it for their own use.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Testing](#testing)
5. [Code Style](#code-style)
6. [Contributing](#contributing)
7. [Extending GrandmaScraper](#extending-grandmascraper)
8. [Release Process](#release-process)

## Development Setup

### Requirements

- Python 3.11+
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/grandma-scraper.git
cd grandma-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install

# Verify installation
pytest
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Ruff
- Even Better TOML

Settings (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true
}
```

#### PyCharm

- Enable Pytest as test runner
- Configure Ruff as external tool
- Set Python interpreter to virtual environment

## Project Structure

```
grandma-scraper/
├── grandma_scraper/          # Main package
│   ├── __init__.py
│   ├── core/                 # Core scraping logic
│   │   ├── __init__.py
│   │   ├── models.py         # Pydantic models
│   │   ├── fetchers.py       # HTML fetching
│   │   ├── extractors.py     # Data extraction
│   │   ├── engine.py         # Orchestration
│   │   └── exporters.py      # Export to files
│   ├── cli/                  # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py           # Typer CLI
│   └── utils/                # Utilities
│       ├── __init__.py
│       ├── robots.py         # robots.txt
│       └── logger.py         # Logging
├── config/                   # Config examples
│   └── examples/
├── tests/                    # Test suite
│   ├── core/
│   ├── cli/
│   ├── e2e/
│   └── fixtures/
├── docs/                     # Documentation
├── pyproject.toml            # Project metadata & deps
├── README.md
└── LICENSE
```

## Development Workflow

### Making Changes

1. **Create a feature branch**

```bash
git checkout -b feature/my-feature
```

2. **Make your changes**

Write code, add tests, update docs.

3. **Run tests**

```bash
pytest
```

4. **Format and lint**

```bash
# Format
black grandma_scraper tests

# Lint
ruff check grandma_scraper tests

# Type check
mypy grandma_scraper
```

5. **Commit**

```bash
git add .
git commit -m "feat: add my feature"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance

6. **Push and create PR**

```bash
git push origin feature/my-feature
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/core/test_models.py

# Specific test function
pytest tests/core/test_models.py::TestScrapeJob::test_minimal_scrape_job

# With coverage
pytest --cov=grandma_scraper --cov-report=html

# Verbose output
pytest -v

# Show print statements
pytest -s
```

### Writing Tests

#### Unit Test Example

```python
# tests/core/test_models.py
import pytest
from pydantic import ValidationError
from grandma_scraper.core.models import FieldConfig

def test_field_config_validation():
    """Test that FieldConfig validates correctly."""
    field = FieldConfig(
        name="title",
        selector=".title",
    )

    assert field.name == "title"
    assert field.selector == ".title"

def test_invalid_custom_attribute():
    """Test that CUSTOM attribute requires custom_attribute."""
    with pytest.raises(ValidationError):
        FieldConfig(
            name="data",
            selector=".data",
            attribute="custom",
            # Missing custom_attribute
        )
```

#### Integration Test Example

```python
# tests/core/test_extractors.py
from pathlib import Path
import pytest
from grandma_scraper.core.extractors import DataExtractor
from grandma_scraper.core.fetchers import HTMLDocument

@pytest.fixture
def sample_html():
    """Load fixture HTML."""
    return Path("tests/fixtures/sample.html").read_text()

def test_extract_basic_fields(sample_html):
    """Test basic field extraction."""
    doc = HTMLDocument(url="http://test.com", html=sample_html)
    extractor = DataExtractor(
        item_selector=".product",
        fields=[
            FieldConfig(name="title", selector=".title"),
        ],
        selector_type="css",
    )

    results = extractor.extract_from_document(doc)
    assert len(results) > 0
    assert "title" in results[0]
```

#### E2E Test Example

```python
# tests/e2e/test_full_scrape.py
import asyncio
import pytest
from grandma_scraper.core import ScrapeJob, ScrapeEngine

@pytest.mark.asyncio
async def test_full_scrape_workflow():
    """Test complete scraping workflow."""
    job = ScrapeJob(
        name="Test Job",
        start_url="http://quotes.toscrape.com/",
        item_selector=".quote",
        fields=[
            FieldConfig(name="text", selector=".text"),
        ],
        max_pages=1,
    )

    engine = ScrapeEngine(job)
    result = await engine.run()

    assert result.status == "completed"
    assert result.total_items > 0
```

### Test Fixtures

Place sample HTML/data in `tests/fixtures/`:

```
tests/fixtures/
├── sample.html           # Sample HTML page
├── sample_with_pagination.html
└── empty_page.html
```

### Mocking

Use `pytest-mock` for mocking external services:

```python
def test_fetcher_with_mock(mocker):
    """Test fetcher with mocked HTTP."""
    mock_response = mocker.Mock()
    mock_response.text = "<html>...</html>"

    mocker.patch('httpx.AsyncClient.get', return_value=mock_response)

    # Test code here
```

## Code Style

### Python Style

We follow:
- **PEP 8** for general style
- **Black** for formatting (line length: 100)
- **Ruff** for linting
- **Type hints** everywhere

### Example

```python
from typing import List, Optional
from pydantic import BaseModel

class MyModel(BaseModel):
    """Model docstring."""

    name: str
    values: List[int]
    description: Optional[str] = None

def process_data(
    data: List[MyModel],
    limit: int = 100,
) -> List[dict]:
    """
    Process data models.

    Args:
        data: List of models to process
        limit: Maximum number to process

    Returns:
        List of processed dictionaries
    """
    results = []
    for item in data[:limit]:
        results.append(item.model_dump())
    return results
```

### Docstrings

Use Google-style docstrings:

```python
def my_function(arg1: str, arg2: int = 0) -> bool:
    """
    Short description.

    Longer description explaining what the function does,
    any important details, edge cases, etc.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2 (default: 0)

    Returns:
        True if successful, False otherwise

    Raises:
        ValueError: If arg1 is empty
        RuntimeError: If processing fails

    Example:
        >>> my_function("test", 42)
        True
    """
    pass
```

### Type Hints

Always use type hints:

```python
# Good
def fetch_data(url: str) -> dict:
    pass

# Bad
def fetch_data(url):
    pass
```

For complex types:

```python
from typing import List, Dict, Optional, Union, Any

def complex_function(
    items: List[Dict[str, Any]],
    mapping: Optional[Dict[str, str]] = None,
) -> Union[List[str], None]:
    pass
```

## Contributing

### Before Contributing

1. Check [issues](https://github.com/yourusername/grandma-scraper/issues) for existing work
2. Discuss major changes in an issue first
3. Read this guide thoroughly

### Contribution Checklist

- [ ] Tests added/updated
- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`)
- [ ] Linting passes (`ruff`)
- [ ] Type checking passes (`mypy`)
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Commit messages follow convention

### Pull Request Process

1. Fork the repository
2. Create your feature branch
3. Make your changes
4. Run all tests and checks
5. Commit your changes
6. Push to your fork
7. Open a Pull Request
8. Address review feedback

### Code Review

We look for:
- **Correctness** - Does it work?
- **Tests** - Is it tested?
- **Style** - Does it follow our style?
- **Documentation** - Is it documented?
- **Performance** - Is it efficient?
- **Security** - Is it safe?

## Extending GrandmaScraper

### Adding a New Fetcher

```python
# grandma_scraper/core/fetchers.py
from grandma_scraper.core.fetchers import HTMLFetcher, HTMLDocument

class MyCustomFetcher(HTMLFetcher):
    """Custom fetcher with special capabilities."""

    async def fetch(self, url: str) -> HTMLDocument:
        """Fetch HTML with custom logic."""
        # Your implementation
        html = await self._custom_fetch(url)
        return HTMLDocument(url=url, html=html)

    async def close(self) -> None:
        """Cleanup resources."""
        # Your cleanup
        pass
```

### Adding a New Export Format

```python
# grandma_scraper/core/exporters.py
class DataExporter:
    # ... existing methods ...

    @staticmethod
    def export_parquet(records: List[Dict[str, Any]], file_path: str) -> None:
        """Export to Parquet format."""
        import pandas as pd

        df = pd.DataFrame(records)
        df.to_parquet(file_path, engine="pyarrow")
```

### Adding a CLI Command

```python
# grandma_scraper/cli/main.py
@app.command()
def my_command(
    arg: str = typer.Argument(..., help="Description"),
) -> None:
    """
    My custom command.

    Example:
        grandma-scraper my-command value
    """
    # Implementation
    console.print(f"Running with {arg}")
```

### Custom Progress Callbacks

```python
from grandma_scraper.core import ScrapeEngine

def my_callback(event_type: str, data: dict) -> None:
    """Custom progress handler."""
    if event_type == "fetching":
        print(f"📄 Fetching page {data['page']}")
    elif event_type == "extracted":
        print(f"✓ Got {data['items_on_page']} items")

engine = ScrapeEngine(job)
result = await engine.run(progress_callback=my_callback)
```

## Release Process

### Version Bumping

1. Update version in `grandma_scraper/__init__.py`
2. Update version in `pyproject.toml`
3. Update `CHANGELOG.md`

### Creating a Release

```bash
# Tag the release
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Build distribution
python -m build

# Upload to PyPI (requires credentials)
python -m twine upload dist/*
```

### Changelog

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [0.2.0] - 2024-01-15

### Added
- New export format: Parquet
- Support for authentication cookies

### Changed
- Improved error messages in CLI

### Fixed
- Bug in pagination URL generation
```

## Debugging

### Debug Logging

```python
from grandma_scraper.utils.logger import setup_logger
import logging

# Enable debug logging
setup_logger(level=logging.DEBUG)
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or with ipdb (better)
import ipdb; ipdb.set_trace()
```

### Playwright Debugging

```python
# Run browser in headed mode
fetcher = BrowserFetcher(headless=False)

# Slow down operations
await page.goto(url, wait_until="networkidle", timeout=60000)
```

## Performance Profiling

### Memory Profiling

```python
from memory_profiler import profile

@profile
def my_function():
    # Your code
    pass
```

### CPU Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)
```

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and discussions
- **Email**: your-email@example.com

## Resources

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)

---

Happy coding! 🚀
