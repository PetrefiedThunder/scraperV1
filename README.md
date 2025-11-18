# 🕷️ GrandmaScraper

> **A production-grade, grandma-friendly web scraping tool**

Point-and-click simple on the surface, powerful under the hood.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What is GrandmaScraper?

GrandmaScraper is a web scraping tool designed with two audiences in mind:

1. **Non-technical users** (like Grandma) who want to:
   - Paste a URL
   - Click what they care about
   - Download a spreadsheet
   - No coding required

2. **Developers and power users** who need:
   - Production-grade scraping engine
   - Modular, tested architecture
   - CLI automation
   - Advanced configuration (pagination, rate limits, browser automation)

## ✨ Features

### For Everyone

- ✅ **Simple CSV/Excel export** - Get your data in familiar formats
- ✅ **Ethical scraping** - Respects robots.txt and rate limits
- ✅ **Visual selector picking** - (Coming in Phase 2) Click elements to scrape them
- ✅ **Progress tracking** - See what's happening in real-time

### For Developers

- ✅ **Modular architecture** - Clean separation of concerns
- ✅ **Multiple backends** - Static (httpx) + Dynamic (Playwright)
- ✅ **Type safety** - Full Pydantic validation
- ✅ **Async-first** - Built on asyncio for performance
- ✅ **Comprehensive tests** - pytest with >80% coverage target
- ✅ **CLI automation** - Integrate with CI/CD pipelines

## 🚀 Quick Start

### For Non-Developers

**1. Install (one-time setup):**

```bash
# Clone or download this repository
git clone https://github.com/yourusername/grandma-scraper.git
cd grandma-scraper

# Install dependencies (requires Python 3.11+)
pip install -e ".[dev]"

# Install Playwright browsers (for dynamic sites)
playwright install chromium
```

**2. Run your first scrape:**

```bash
# Use one of the example configs
grandma-scraper run config/examples/example-quotes.yaml -o my-quotes.csv

# View the results in Excel or any spreadsheet program!
```

**3. Create your own scraper:**

```bash
# Generate a template config
grandma-scraper init "My Scraper" "https://example.com" -o my-config.yaml

# Edit my-config.yaml with your favorite text editor
# Run it!
grandma-scraper run my-config.yaml -o results.xlsx
```

### For Developers

**Installation:**

```bash
# Clone repository
git clone https://github.com/yourusername/grandma-scraper.git
cd grandma-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install

# Run tests
pytest
```

**Basic Usage:**

```python
import asyncio
from grandma_scraper.core import ScrapeJob, ScrapeEngine
from grandma_scraper.core.models import FieldConfig

# Define your scrape job
job = ScrapeJob(
    name="Example Scraper",
    start_url="https://quotes.toscrape.com/",
    item_selector=".quote",
    fields=[
        FieldConfig(name="text", selector=".text"),
        FieldConfig(name="author", selector=".author"),
    ],
)

# Run the scrape
async def main():
    engine = ScrapeEngine(job)
    result = await engine.run()
    print(f"Collected {result.total_items} items!")
    return result

result = asyncio.run(main())
```

## 📖 Documentation

- **[User Guide](docs/USER_GUIDE.md)** - Step-by-step tutorials for non-technical users
- **[Developer Guide](docs/DEV_GUIDE.md)** - Architecture, testing, contributing
- **[Architecture](docs/ARCHITECTURE.md)** - System design and module descriptions
- **[Configuration Guide](docs/HOW_TO_ADD_NEW_SITES.md)** - Create custom scraper configs

## 🛠️ CLI Commands

```bash
# Run a scrape job from config
grandma-scraper run <config-file> -o <output-file>

# Validate a configuration file
grandma-scraper validate <config-file>

# Create a new config template
grandma-scraper init "Job Name" "https://example.com" -o config.yaml

# Show version
grandma-scraper --version

# Get help
grandma-scraper --help
```

## 📋 Example Configuration

```yaml
# config/my-scraper.yaml
name: "Product Scraper"
description: "Scrape product listings"
start_url: "https://example.com/products"

# What to scrape
item_selector: ".product"
fields:
  - name: "title"
    selector: ".product-title"
    attribute: "text"
    required: true

  - name: "price"
    selector: ".price"
    attribute: "text"

  - name: "image"
    selector: "img"
    attribute: "src"

# Pagination
pagination:
  type: "next_button"
  next_button_selector: ".next-page"

# Limits
max_pages: 10
max_items: 100

# Be polite!
min_delay_ms: 1000
max_delay_ms: 2000
respect_robots_txt: true
```

## 🎓 Learning Path

### Beginner: Use Example Configs

1. Start with `config/examples/example-quotes.yaml`
2. Run it: `grandma-scraper run config/examples/example-quotes.yaml -o quotes.csv`
3. Open `quotes.csv` in Excel
4. Modify the config to scrape different fields

### Intermediate: Create Custom Configs

1. Generate a template: `grandma-scraper init "My Scraper" "https://mysite.com"`
2. Learn CSS selectors (see [User Guide](docs/USER_GUIDE.md))
3. Test selectors with browser DevTools
4. Run and iterate

### Advanced: Use Python API

1. Import `grandma_scraper` in your scripts
2. Create `ScrapeJob` programmatically
3. Implement custom progress callbacks
4. Extend with custom exporters or fetchers

## ⚖️ Ethical Scraping

**GrandmaScraper is designed for responsible, legal scraping.**

- ✅ **Respects robots.txt** (by default)
- ✅ **Rate limiting** to avoid overloading servers
- ✅ **User-agent transparency** (not hiding as a browser)
- ✅ **Clear warnings** when scraping might be restricted

**Important:**
- Always check a website's Terms of Service
- Respect copyright and data protection laws
- Don't scrape personal or sensitive information
- Use appropriate rate limits
- Consider reaching out to sites for API access first

**This tool is for:**
- ✅ Public data research
- ✅ Academic projects
- ✅ Personal use
- ✅ Data journalism
- ✅ Authorized testing

**Not for:**
- ❌ Bypassing paywalls
- ❌ Scraping private/protected content
- ❌ Competitive intelligence without permission
- ❌ Bulk email harvesting
- ❌ Any illegal activity

## 🏗️ Architecture

```
grandma_scraper/
├── core/               # Scraping engine
│   ├── models.py      # Data models (Pydantic)
│   ├── fetchers.py    # HTML fetching (requests + Playwright)
│   ├── extractors.py  # Data extraction (CSS/XPath)
│   ├── engine.py      # Main orchestration
│   └── exporters.py   # CSV/JSON/Excel export
├── cli/               # Command-line interface
│   └── main.py        # Typer CLI app
└── utils/             # Utilities
    ├── robots.py      # robots.txt checker
    └── logger.py      # Logging setup
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design docs.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=grandma_scraper --cov-report=html

# Run specific test file
pytest tests/core/test_models.py

# Run with verbose output
pytest -v
```

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/) for browser automation
- [Pydantic](https://docs.pydantic.dev/) for data validation
- [FastAPI](https://fastapi.tiangolo.com/) for future API endpoints
- [Typer](https://typer.tiangolo.com/) for beautiful CLIs

## 📮 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/grandma-scraper/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/grandma-scraper/discussions)
- **Email:** your-email@example.com

---

**Made with ❤️ for ethical web scraping**

*Remember: With great scraping power comes great responsibility!*
