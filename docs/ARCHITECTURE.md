# Architecture Documentation

This document describes the architecture and design of GrandmaScraper.

## Design Principles

1. **Separation of Concerns** - Each module has a single, well-defined responsibility
2. **Type Safety** - Pydantic models ensure runtime validation
3. **Async-First** - Built on asyncio for concurrent operations
4. **Testability** - Clean interfaces make unit testing straightforward
5. **Extensibility** - Plugin points for custom fetchers, exporters, etc.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI / UI Layer                       │
│                  (Typer CLI or Future Web UI)                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Scrape Engine                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Fetchers │  │Extractor │  │Pagination│  │ Robots   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Storage Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │   CSV    │  │   JSON   │  │  Excel   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Models (`grandma_scraper/core/models.py`)

**Purpose:** Define data structures with validation

**Key Classes:**

- `ScrapeJob` - Complete configuration for a scrape
  - Validates URLs, selectors, limits
  - Ensures pagination config is valid
  - Provides sensible defaults

- `FieldConfig` - Configuration for extracting a single field
  - Supports CSS and XPath selectors
  - Multiple attribute types (text, href, src, custom)
  - Required vs optional fields

- `PaginationStrategy` - How to handle multiple pages
  - Types: NONE, NEXT_BUTTON, URL_PATTERN, INFINITE_SCROLL
  - Type-specific validation

- `ScrapeResult` - Results and metadata from execution
  - Status tracking (pending, running, completed, failed)
  - Timing information
  - Error details and warnings

**Design Notes:**
- Uses Pydantic for validation and serialization
- Immutable where possible (prevents accidental modification)
- Self-validating (raises errors early, before scraping starts)

### 2. Fetchers (`grandma_scraper/core/fetchers.py`)

**Purpose:** Retrieve HTML content from URLs

**Architecture:**

```python
HTMLFetcher (Abstract Base Class)
    ├── RequestsFetcher    # Fast, static HTML only
    ├── BrowserFetcher     # Slower, handles JavaScript
    └── AutoFetcher        # Smart selection between the two
```

**Key Classes:**

- `HTMLDocument` - Wrapper around HTML with parsing
  - Lazy-loads BeautifulSoup
  - Provides consistent interface
  - Caches parsed tree

- `RequestsFetcher` - Uses httpx for simple requests
  - Best for: Static HTML, APIs
  - Not for: SPAs, JS-heavy sites
  - Very fast, low memory

- `BrowserFetcher` - Uses Playwright for full browser
  - Best for: JavaScript sites, SPAs
  - Handles: Infinite scroll, dynamic content
  - Features: Stealth mode, screenshot capability (future)

- `AutoFetcher` - Tries requests first, falls back to browser
  - Heuristics: page size, SPA indicators
  - Best of both worlds for mixed workloads

**Design Notes:**
- Async context managers for resource cleanup
- Random user agent rotation
- Stealth scripts to avoid detection

### 3. Extractors (`grandma_scraper/core/extractors.py`)

**Purpose:** Extract structured data from HTML

**Key Class:** `DataExtractor`

**Workflow:**

1. Find all "item" containers using item_selector
2. For each container:
   - Extract each field using its selector
   - Handle required vs optional fields
   - Apply default values
   - Skip items missing required fields
3. Return list of records (dicts)

**Features:**
- CSS and XPath selector support (via lxml)
- Multiple value extraction (arrays)
- Attribute extraction (href, src, custom)
- Validation mode (test selectors on sample)

**Design Notes:**
- Uses lxml for robust parsing
- Graceful error handling (skip bad items, don't crash)
- Validation helper for debugging selectors

### 4. Engine (`grandma_scraper/core/engine.py`)

**Purpose:** Orchestrate the entire scraping process

**Key Class:** `ScrapeEngine`

**Responsibilities:**

1. **Pre-flight checks**
   - Validate robots.txt (if enabled)
   - Choose appropriate fetcher

2. **Scraping loop**
   - Fetch page
   - Extract data
   - Handle pagination
   - Respect rate limits
   - Track progress

3. **Error handling**
   - Retry on transient failures
   - Collect warnings
   - Graceful degradation

4. **Progress reporting**
   - Callback system for UI updates
   - Event types: started, fetching, extracted, completed, failed

**Design Notes:**
- State machine for scrape lifecycle
- Progress callbacks don't block scraping
- Can be stopped gracefully mid-scrape

### 5. Exporters (`grandma_scraper/core/exporters.py`)

**Purpose:** Save scraped data to files

**Key Class:** `DataExporter`

**Supported Formats:**
- CSV - Universal, simple
- JSON - Structured, preserves types
- Excel (.xlsx) - User-friendly for non-technical users

**Features:**
- Auto-detect format from file extension
- Create parent directories automatically
- Handle empty datasets gracefully
- Excel: Auto-adjust column widths

**Design Notes:**
- Pandas for Excel (openpyxl engine)
- Standard library csv/json for others
- Consistent error handling

### 6. Utilities

#### Robots Checker (`grandma_scraper/utils/robots.py`)

**Purpose:** Respect robots.txt directives

**Key Class:** `RobotsChecker`

**Features:**
- Fetch and parse robots.txt
- Cache per domain
- Check specific URL paths
- Default to allow if robots.txt unavailable

**Design Notes:**
- Uses stdlib `robotparser`
- Async with caching for performance
- Fail open (allow if error) for usability

#### Logger (`grandma_scraper/utils/logger.py`)

**Purpose:** Structured logging with rich formatting

**Features:**
- Console output with Rich (colored, formatted)
- Optional file logging
- Tracebacks with local variables
- Configurable log levels

## Data Flow

### Typical Scrape Execution

```
1. User provides ScrapeJob config
        ↓
2. ScrapeEngine.run() called
        ↓
3. Check robots.txt (if enabled)
        ↓
4. Create fetcher and extractor
        ↓
5. FOR EACH page:
    a. Fetch HTML (fetcher)
    b. Extract items (extractor)
    c. Add to results
    d. Check limits (max_pages, max_items)
    e. Get next page URL (pagination)
    f. Polite delay
        ↓
6. Mark completed
        ↓
7. Return ScrapeResult
        ↓
8. Export to file (if requested)
```

## Extension Points

### Adding a New Fetcher

```python
from grandma_scraper.core.fetchers import HTMLFetcher, HTMLDocument

class MyCustomFetcher(HTMLFetcher):
    async def fetch(self, url: str) -> HTMLDocument:
        # Your custom logic
        html = ...
        return HTMLDocument(url=url, html=html)

    async def close(self) -> None:
        # Cleanup
        pass
```

### Adding a New Exporter

```python
from grandma_scraper.core.exporters import DataExporter

# Add method to DataExporter
@staticmethod
def export_xml(records, file_path):
    # Your export logic
    pass
```

### Custom Progress Tracking

```python
def my_progress_callback(event_type: str, data: dict):
    if event_type == "fetching":
        print(f"Fetching page {data['page']}")
    elif event_type == "extracted":
        print(f"Got {data['items_on_page']} items")

result = await engine.run(progress_callback=my_progress_callback)
```

## Performance Considerations

### Concurrency

- **Current:** Sequential page fetching
- **Future:** Concurrent page fetching with semaphore
- **Consideration:** Respect `concurrent_requests` setting

### Memory

- **Streaming parsers** for large HTML documents
- **Result batching** for very large datasets
- **Browser cleanup** - close contexts between pages

### Caching

- **Robots.txt** - cached per domain
- **DNS resolution** - httpx handles this
- **Future:** Optional HTTP cache

## Security Considerations

1. **Input Validation**
   - Pydantic validates all configs
   - URL schemes checked
   - Selector syntax validated at runtime

2. **Resource Limits**
   - Timeouts on all network requests
   - Max pages/items limits
   - File size limits (future)

3. **Safe Defaults**
   - robots.txt enabled by default
   - Rate limiting enabled by default
   - Transparent user agents

## Future Enhancements

### Phase 2: Web UI

- Visual selector picker
- Real-time preview
- Drag-and-drop config builder

### Phase 3: Advanced Features

- Scheduling (cron-like)
- Authentication (cookies, OAuth)
- Data transformation pipelines
- Webhook notifications

### Phase 4: Scalability

- Distributed scraping (Celery/RQ)
- Cloud storage backends (S3, GCS)
- Database integration (PostgreSQL, MongoDB)
- Horizontal scaling

## Testing Strategy

### Unit Tests

- **Models:** Validation logic
- **Extractors:** Selector matching, field extraction
- **Exporters:** File format correctness

### Integration Tests

- **Engine:** Full scrape workflow
- **Fetchers:** Network requests (with mocks)
- **CLI:** Command execution

### E2E Tests

- Real websites (test sites like quotes.toscrape.com)
- Full pipeline: config → scrape → export

## Configuration Management

### Config File Formats

- YAML (primary, human-friendly)
- JSON (machine-friendly)

### Config Schema

- Defined by Pydantic models
- Self-documenting via model docstrings
- Exportable as JSON Schema

### Config Validation

```bash
grandma-scraper validate config.yaml
```

## Logging and Monitoring

### Log Levels

- **DEBUG:** Detailed execution flow
- **INFO:** High-level progress
- **WARNING:** Non-fatal issues (robots.txt violations, missing fields)
- **ERROR:** Fatal errors (network failures, parsing errors)

### Metrics (Future)

- Items/second
- Success rate
- Error types
- Resource usage

## Error Handling Philosophy

1. **Fail early on config errors** - Don't start scraping with bad config
2. **Graceful degradation on runtime errors** - Skip bad items, continue scraping
3. **Collect warnings** - Report issues without stopping
4. **Clear error messages** - Guide user to resolution

## Code Organization

```
grandma_scraper/
├── __init__.py           # Package metadata
├── core/                 # Core scraping logic
│   ├── __init__.py
│   ├── models.py         # Data models
│   ├── fetchers.py       # HTML fetching
│   ├── extractors.py     # Data extraction
│   ├── engine.py         # Main orchestration
│   └── exporters.py      # Export to files
├── cli/                  # Command-line interface
│   ├── __init__.py
│   └── main.py           # Typer CLI app
└── utils/                # Utilities
    ├── __init__.py
    ├── robots.py         # robots.txt checking
    └── logger.py         # Logging setup
```

## Dependencies

### Core
- `playwright` - Browser automation
- `beautifulsoup4` + `lxml` - HTML parsing
- `pydantic` - Data validation
- `httpx` - HTTP client

### CLI
- `typer` - CLI framework
- `rich` - Terminal formatting
- `pyyaml` - YAML parsing

### Export
- `pandas` + `openpyxl` - Excel export

### Dev
- `pytest` - Testing
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

## Versioning

- **Semantic Versioning:** MAJOR.MINOR.PATCH
- **Breaking changes:** Bump MAJOR
- **New features:** Bump MINOR
- **Bug fixes:** Bump PATCH

Current: 0.1.0 (Phase 1 - Core Engine)
