# User Guide

Welcome to GrandmaScraper! This guide will help you start scraping websites, even if you've never written code before.

## Table of Contents

1. [Installation](#installation)
2. [Your First Scrape](#your-first-scrape)
3. [Understanding the Results](#understanding-the-results)
4. [Creating Your Own Scrapers](#creating-your-own-scrapers)
5. [Finding Selectors](#finding-selectors)
6. [Common Patterns](#common-patterns)
7. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

You need Python 3.11 or newer. Check your version:

```bash
python --version
```

If you don't have Python, download it from [python.org](https://www.python.org/downloads/).

### Step-by-Step Installation

**1. Download GrandmaScraper**

```bash
# If you have git:
git clone https://github.com/yourusername/grandma-scraper.git
cd grandma-scraper

# Or download the ZIP file and extract it
```

**2. Install GrandmaScraper**

```bash
pip install -e ".[dev]"
```

This might take a few minutes. You'll see lots of text scroll by - that's normal!

**3. Install the browser**

```bash
playwright install chromium
```

This downloads a special browser that GrandmaScraper uses.

**4. Test the installation**

```bash
grandma-scraper --version
```

You should see: `GrandmaScraper version 0.1.0`

## Your First Scrape

Let's scrape some inspirational quotes!

**Step 1: Run the example scraper**

```bash
grandma-scraper run config/examples/example-quotes.yaml -o my-quotes.csv
```

**What happens:**
- GrandmaScraper visits http://quotes.toscrape.com
- It finds all quotes on the first 3 pages
- It saves them to `my-quotes.csv`

**Step 2: Open the results**

Open `my-quotes.csv` in Excel, Google Sheets, or any spreadsheet program.

You should see columns:
- `text` - The quote
- `author` - Who said it
- `tags` - Keywords

Congratulations! You just scraped your first website! 🎉

## Understanding the Results

### What Files Did It Create?

- **my-quotes.csv** - Your scraped data

### What Did The Scraper Do?

1. **Visited the website** - Like opening it in a browser
2. **Found the quotes** - Used "selectors" to find the right parts
3. **Extracted the data** - Pulled out text, author, tags
4. **Went to next page** - Clicked "Next" automatically
5. **Saved everything** - Wrote to a CSV file

### Reading the Output

When you run a scraper, you'll see messages like:

```
Loading config from: config/examples/example-quotes.yaml
✓ Loaded job: Quotes to Scrape - Example
  Start URL: http://quotes.toscrape.com/
  Fields: text, author, tags

Starting scrape...
Fetching page 1...
Extracted 10 items from 1 pages...
Fetching page 2...
Extracted 20 items from 2 pages...

✓ Scrape completed successfully!
  Items collected: 30
  Pages scraped: 3
  Duration: 4.23s

Exporting to: my-quotes.csv
✓ Export complete!
```

## Creating Your Own Scrapers

### Method 1: Start From a Template

```bash
grandma-scraper init "My Scraper" "https://example.com" -o my-scraper.yaml
```

This creates a file called `my-scraper.yaml` with a basic template.

### Method 2: Copy an Example

```bash
cp config/examples/example-quotes.yaml config/my-scraper.yaml
```

Then edit `my-scraper.yaml` with any text editor.

### The Config File Explained

Here's a simple config file with explanations:

```yaml
# Name your scraper
name: "Product Price Tracker"

# What website are we scraping?
start_url: "https://example.com/products"

# What container holds each item?
# (In this case, each product is in a <div class="product">)
item_selector: ".product"

# What information do we want from each item?
fields:
  # The product name
  - name: "product_name"
    selector: ".title"           # Where to find it
    attribute: "text"            # Get the text inside
    required: true               # Skip items without this

  # The price
  - name: "price"
    selector: ".price"
    attribute: "text"

  # The product image
  - name: "image_url"
    selector: "img"              # Find the <img> tag
    attribute: "src"             # Get the src attribute (URL)

# How to get to the next page?
pagination:
  type: "next_button"
  next_button_selector: ".next"  # Click the "Next" button

# Limits (so you don't scrape forever)
max_pages: 5                     # Only scrape 5 pages
max_items: 100                   # Stop after 100 products

# Be polite to websites
min_delay_ms: 1000               # Wait 1-2 seconds between pages
max_delay_ms: 2000
respect_robots_txt: true         # Check if scraping is allowed
```

## Finding Selectors

Selectors tell GrandmaScraper where to find information on the page.

### Method: Using Browser DevTools

**Step 1: Open the website in Chrome or Firefox**

**Step 2: Right-click on the element you want → "Inspect"**

You'll see code that looks like:

```html
<div class="product">
  <h2 class="title">Laptop Pro</h2>
  <span class="price">$999</span>
</div>
```

**Step 3: Identify the selector**

- The product container: `.product` (the dot means "class")
- The title: `.title`
- The price: `.price`

### Common Selector Patterns

| What | Selector | Example |
|------|----------|---------|
| Class | `.classname` | `.product`, `.title` |
| ID | `#idname` | `#main-content` |
| Tag | `tagname` | `h1`, `p`, `img` |
| Combination | `tag.class` | `div.product`, `h2.title` |
| Child | `parent > child` | `.product > .title` |
| Descendant | `ancestor descendant` | `.product .price` |

### Testing Selectors in the Browser

In the browser console (F12 → Console tab):

```javascript
// Test if selector finds elements
document.querySelectorAll('.product')
// Should show all matching elements
```

## Common Patterns

### Pattern 1: Simple List

**Example:** A list of articles

```yaml
item_selector: ".article"
fields:
  - name: "title"
    selector: "h2"
    attribute: "text"

  - name: "link"
    selector: "a"
    attribute: "href"
```

### Pattern 2: Product Catalog

**Example:** E-commerce products

```yaml
item_selector: ".product-card"
fields:
  - name: "name"
    selector: ".product-title"
    attribute: "text"

  - name: "price"
    selector: ".price"
    attribute: "text"

  - name: "image"
    selector: "img"
    attribute: "src"

  - name: "rating"
    selector: ".rating"
    attribute: "text"
```

### Pattern 3: Pagination with Page Numbers

**Example:** URLs like `?page=1`, `?page=2`

```yaml
pagination:
  type: "url_pattern"
  url_pattern: "?page={page}"

max_pages: 10
```

### Pattern 4: Multiple Values

**Example:** Get all tags/categories for an item

```yaml
fields:
  - name: "categories"
    selector: ".category"
    attribute: "text"
    multiple: true    # Get ALL categories, not just first one
```

## Troubleshooting

### Problem: "No items were collected"

**Possible causes:**

1. **Wrong item selector**
   - **Fix:** Open the website, inspect the elements, verify the selector

2. **JavaScript-loaded content**
   - **Fix:** Change `fetcher_type` to `"browser"` in your config:
   ```yaml
   fetcher_type: "browser"
   ```

3. **Website requires login**
   - **Fix:** GrandmaScraper can't log in yet (coming in Phase 4)

### Problem: "Some fields are empty"

**Possible causes:**

1. **Wrong field selector**
   - **Fix:** Double-check the selector in browser DevTools

2. **Field doesn't exist on all items**
   - **Fix:** Make it optional:
   ```yaml
   - name: "description"
     selector: ".desc"
     required: false        # Don't skip item if missing
     default_value: "N/A"   # Use this if not found
   ```

### Problem: "Scraper is too slow"

**Solutions:**

1. **Use requests instead of browser** (if site doesn't need JavaScript):
   ```yaml
   fetcher_type: "requests"
   ```

2. **Reduce delays** (but be careful - don't overwhelm the site):
   ```yaml
   min_delay_ms: 500
   max_delay_ms: 1000
   ```

3. **Limit pages**:
   ```yaml
   max_pages: 3
   ```

### Problem: "robots.txt disallows scraping"

**What it means:** The website doesn't want to be scraped.

**Options:**

1. **Respect it** - Don't scrape that site
2. **Check if API available** - Many sites offer APIs
3. **Override** (use responsibly!):
   ```yaml
   respect_robots_txt: false
   ```

### Problem: "Too many requests / IP blocked"

**Cause:** Scraping too aggressively

**Fixes:**

1. **Increase delays**:
   ```yaml
   min_delay_ms: 3000
   max_delay_ms: 5000
   ```

2. **Reduce concurrent requests**:
   ```yaml
   concurrent_requests: 1
   ```

3. **Take breaks** - Don't run the scraper continuously

## Tips for Success

### 1. Start Small

- Test on 1-2 pages first
- Set `max_pages: 2` while testing
- Once it works, increase the limit

### 2. Be Polite

- Use reasonable delays (1-2 seconds minimum)
- Don't scrape the same site repeatedly
- Respect robots.txt

### 3. Test Selectors First

- Use browser DevTools to verify selectors
- Run `grandma-scraper validate config.yaml` before scraping

### 4. Check the Output

- Open the CSV/Excel file after scraping
- Make sure the data looks correct
- Adjust selectors if needed

### 5. Save Your Configs

- Keep your config files in `config/`
- Name them descriptively: `amazon-books.yaml`, `news-articles.yaml`
- Add comments to remember what they do

## Getting Help

### Validate Your Config

```bash
grandma-scraper validate my-scraper.yaml
```

This checks for errors before you run it.

### Run in Verbose Mode

```bash
grandma-scraper run my-scraper.yaml -o output.csv --verbose
```

Shows detailed information about what's happening.

### Check the Logs

If something goes wrong, look at the error messages. They usually tell you what's wrong.

## Next Steps

Once you're comfortable with basic scraping:

1. **Read [HOW_TO_ADD_NEW_SITES.md](HOW_TO_ADD_NEW_SITES.md)** - Advanced patterns
2. **Learn XPath** - Alternative to CSS selectors (more powerful)
3. **Automate scraping** - Run scrapers on a schedule (cron)
4. **Use the Python API** - Integrate into your own scripts

## Legal and Ethical Notes

**Always:**
- Check the website's Terms of Service
- Respect robots.txt
- Use reasonable rate limits
- Don't scrape personal information
- Give credit when publishing scraped data

**Never:**
- Bypass paywalls
- Scrape private/login-protected content without permission
- Overwhelm small websites
- Use scraped data for spam or malicious purposes

---

Happy scraping! Remember: be curious, be respectful, be responsible. 🕷️
