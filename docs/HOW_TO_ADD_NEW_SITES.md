# How to Add New Sites

This guide explains how to create scraper configurations for new websites.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Analyzing the Target Site](#analyzing-the-target-site)
3. [Configuration Patterns](#configuration-patterns)
4. [Advanced Techniques](#advanced-techniques)
5. [Testing Your Config](#testing-your-config)
6. [Common Challenges](#common-challenges)

## Quick Start

### Step 1: Generate Template

```bash
grandma-scraper init "Site Name" "https://example.com" -o config/my-site.yaml
```

### Step 2: Analyze the Site

Open the site in your browser and inspect the HTML structure.

### Step 3: Update Config

Edit `config/my-site.yaml` with the correct selectors.

### Step 4: Test

```bash
grandma-scraper validate config/my-site.yaml
grandma-scraper run config/my-site.yaml -o test.csv
```

## Analyzing the Target Site

### Finding Item Containers

**Goal:** Find the HTML element that wraps each "item" (product, article, listing, etc.)

**Method:**

1. Open the target page in Chrome/Firefox
2. Right-click on an item → "Inspect"
3. Look for a common parent element

**Example:**

```html
<!-- Good: All products are in .product-card -->
<div class="product-card">
  <h3>Product Name</h3>
  <span class="price">$99</span>
</div>

<div class="product-card">
  <h3>Another Product</h3>
  <span class="price">$149</span>
</div>
```

**Config:**

```yaml
item_selector: ".product-card"
```

### Finding Field Selectors

**For each field you want to extract:**

1. Inspect the element
2. Note the class, ID, or tag
3. Test the selector in browser console:

```javascript
// Test if selector works
document.querySelector('.product-card .price').textContent
// Should return: "$99"
```

### Choosing Attribute Type

| You Want | Use Attribute |
|----------|---------------|
| Visible text | `text` |
| Link URL | `href` |
| Image URL | `src` |
| Button value | `value` |
| Custom attribute | `custom` |

**Examples:**

```yaml
# Get text
- name: "title"
  selector: "h3"
  attribute: "text"

# Get link
- name: "url"
  selector: "a"
  attribute: "href"

# Get image
- name: "image"
  selector: "img"
  attribute: "src"

# Get custom attribute
- name: "product_id"
  selector: ".product"
  attribute: "custom"
  custom_attribute: "data-product-id"
```

## Configuration Patterns

### Pattern 1: Simple List (No Pagination)

**Use case:** Blog posts on a single page

```yaml
name: "Blog Posts"
start_url: "https://blog.example.com"

item_selector: ".post"
fields:
  - name: "title"
    selector: "h2"
    attribute: "text"

  - name: "excerpt"
    selector: ".excerpt"
    attribute: "text"

  - name: "link"
    selector: "a.read-more"
    attribute: "href"

# No pagination
pagination:
  type: "none"

max_pages: 1
```

### Pattern 2: Next Button Pagination

**Use case:** Product catalog with "Next" button

```yaml
name: "Product Catalog"
start_url: "https://shop.example.com/products"

item_selector: ".product"
fields:
  - name: "name"
    selector: ".product-name"
    attribute: "text"

  - name: "price"
    selector: ".price"
    attribute: "text"

pagination:
  type: "next_button"
  next_button_selector: "a.next-page"
  # or: ".pagination .next"
  # or: "button[aria-label='Next']"

max_pages: 10
```

### Pattern 3: URL Pattern Pagination

**Use case:** Pages with numbered URLs

**URL Examples:**
- `https://site.com/page/1`
- `https://site.com/page/2`
- `https://site.com?page=1`

```yaml
name: "News Articles"
start_url: "https://news.example.com?page=1"

item_selector: ".article"
fields:
  - name: "headline"
    selector: "h2"
    attribute: "text"

pagination:
  type: "url_pattern"
  url_pattern: "?page={page}"
  # The {page} will be replaced with 1, 2, 3, etc.

max_pages: 20
```

### Pattern 4: Multiple Values

**Use case:** Items with multiple tags, categories, or images

```yaml
name: "Recipes"
start_url: "https://recipes.example.com"

item_selector: ".recipe"
fields:
  - name: "title"
    selector: "h2"
    attribute: "text"

  # Single value
  - name: "author"
    selector: ".author"
    attribute: "text"

  # Multiple values (list)
  - name: "tags"
    selector: ".tag"
    attribute: "text"
    multiple: true  # Returns array of all tags

  - name: "images"
    selector: ".gallery img"
    attribute: "src"
    multiple: true  # Returns array of all image URLs
```

### Pattern 5: Nested Selectors

**Use case:** Data within specific containers

```yaml
name: "Job Listings"
start_url: "https://jobs.example.com"

item_selector: ".job-posting"
fields:
  # Direct child
  - name: "title"
    selector: "> h3"  # Direct child h3
    attribute: "text"

  # Nested deep
  - name: "company"
    selector: ".details .company-name"
    attribute: "text"

  # Multiple levels
  - name: "salary"
    selector: ".job-info .salary-range span"
    attribute: "text"
```

### Pattern 6: Required vs Optional Fields

**Use case:** Some items have data, others don't

```yaml
fields:
  # Required - skip item if missing
  - name: "title"
    selector: ".title"
    attribute: "text"
    required: true

  # Optional with default
  - name: "rating"
    selector: ".rating"
    attribute: "text"
    required: false
    default_value: "Not rated"

  # Optional without default (will be null)
  - name: "discount"
    selector: ".discount"
    attribute: "text"
    required: false
```

## Advanced Techniques

### XPath Selectors

**When to use:** Complex selections CSS can't handle

```yaml
item_selector: "//div[@class='product']"
item_selector_type: "xpath"

fields:
  - name: "price"
    selector: "//span[contains(@class, 'price')]/text()"
    selector_type: "xpath"
    attribute: "text"
```

### Dynamic Sites (JavaScript)

**Problem:** Content loads with JavaScript

**Solution:** Use browser fetcher

```yaml
fetcher_type: "browser"  # Instead of "requests"
timeout_seconds: 60      # Give JavaScript time to load
```

### Handling Rate Limits

**Be polite to avoid getting blocked:**

```yaml
# Delays between requests
min_delay_ms: 2000      # 2 seconds minimum
max_delay_ms: 5000      # 5 seconds maximum

# Only 1 request at a time
concurrent_requests: 1

# Respect robots.txt
respect_robots_txt: true
```

### Custom User Agents

```yaml
user_agents:
  - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
  # Rotates between these
```

## Testing Your Config

### Step 1: Validate Syntax

```bash
grandma-scraper validate config/my-site.yaml
```

**Checks:**
- YAML syntax
- Required fields
- Type constraints

### Step 2: Test on One Page

Set `max_pages: 1` temporarily:

```yaml
max_pages: 1
max_items: 10
```

Run:

```bash
grandma-scraper run config/my-site.yaml -o test.csv
```

### Step 3: Check Output

Open `test.csv`:
- Are all fields present?
- Is the data correct?
- Any empty/null values?

### Step 4: Adjust Selectors

If data is missing:

1. Check selector in browser console:
   ```javascript
   document.querySelectorAll('.product .price')
   ```

2. Update config

3. Re-test

### Step 5: Test Pagination

Once one page works, test pagination:

```yaml
max_pages: 3
```

Verify:
- Multiple pages are scraped
- No duplicate items
- Pagination stops correctly

## Common Challenges

### Challenge 1: No Items Found

**Possible causes:**

1. **Wrong item selector**
   - **Debug:** Test in console: `document.querySelectorAll('.item')`
   - **Fix:** Update `item_selector`

2. **Content loads with JavaScript**
   - **Debug:** View source (Ctrl+U) - is content there?
   - **Fix:** Set `fetcher_type: "browser"`

3. **Items in shadow DOM**
   - **Debug:** Check if content is in shadow root
   - **Fix:** May need custom scraper (advanced)

### Challenge 2: Empty Fields

**Possible causes:**

1. **Wrong field selector**
   - **Debug:** Inspect element, verify selector
   - **Fix:** Update field selector

2. **Attribute type wrong**
   - **Debug:** Is it text content or an attribute?
   - **Fix:** Change `attribute` (text vs href vs src)

3. **Field not in all items**
   - **Fix:** Set `required: false`

### Challenge 3: Pagination Not Working

**Next button pagination:**

```yaml
# Make sure selector is correct
pagination:
  type: "next_button"
  next_button_selector: "a.next"  # Test this in console!
```

**URL pattern pagination:**

```yaml
# Make sure pattern matches
pagination:
  type: "url_pattern"
  url_pattern: "?page={page}"
  # Start URL should be page 1: https://example.com?page=1
```

### Challenge 4: Getting Blocked

**Symptoms:**
- 403 Forbidden errors
- 429 Too Many Requests
- CAPTCHAs

**Solutions:**

1. **Increase delays:**
   ```yaml
   min_delay_ms: 5000
   max_delay_ms: 10000
   ```

2. **Reduce requests:**
   ```yaml
   max_pages: 5
   concurrent_requests: 1
   ```

3. **Check robots.txt:**
   ```bash
   curl https://example.com/robots.txt
   ```

4. **Consider alternatives:**
   - Use their API if available
   - Contact them for permission
   - Scrape less frequently

### Challenge 5: Dynamic Content

**Problem:** Content appears after scrolling/clicking

**Solutions:**

1. **Use browser fetcher:**
   ```yaml
   fetcher_type: "browser"
   ```

2. **Infinite scroll:**
   ```yaml
   pagination:
     type: "infinite_scroll"
     max_scrolls: 10
     scroll_wait_ms: 2000
   ```

3. **Click to load more:**
   - Current version doesn't support this
   - Coming in future version

## Real-World Examples

### Example 1: Hacker News

```yaml
name: "Hacker News Front Page"
start_url: "https://news.ycombinator.com/"

item_selector: "tr.athing"
fields:
  - name: "title"
    selector: ".titleline > a"
    attribute: "text"

  - name: "url"
    selector: ".titleline > a"
    attribute: "href"

pagination:
  type: "none"

max_items: 30
min_delay_ms: 2000
```

### Example 2: Quotes to Scrape

```yaml
name: "Quotes"
start_url: "http://quotes.toscrape.com/"

item_selector: ".quote"
fields:
  - name: "text"
    selector: ".text"
    attribute: "text"

  - name: "author"
    selector: ".author"
    attribute: "text"

  - name: "tags"
    selector: ".tag"
    attribute: "text"
    multiple: true

pagination:
  type: "next_button"
  next_button_selector: ".next > a"

max_pages: 5
```

### Example 3: E-commerce Products

```yaml
name: "Product Catalog"
start_url: "https://shop.example.com/products?page=1"

item_selector: ".product-grid-item"
fields:
  - name: "name"
    selector: ".product-title"
    attribute: "text"
    required: true

  - name: "price"
    selector: ".price"
    attribute: "text"

  - name: "original_price"
    selector: ".original-price"
    attribute: "text"
    required: false

  - name: "image"
    selector: ".product-image img"
    attribute: "src"

  - name: "link"
    selector: "a.product-link"
    attribute: "href"

pagination:
  type: "url_pattern"
  url_pattern: "?page={page}"

max_pages: 20
max_items: 500

fetcher_type: "auto"
min_delay_ms: 1500
max_delay_ms: 3000
```

## Best Practices

### 1. Start Simple

- Scrape 1 page first
- Add 1 field at a time
- Test frequently

### 2. Be Specific

- Use specific selectors (classes > tags)
- Avoid overly broad selectors
- Test edge cases

### 3. Handle Missing Data

- Set `required: false` for optional fields
- Use `default_value` when appropriate
- Check output for nulls

### 4. Be Polite

- Use realistic delays (2-5 seconds)
- Don't scrape continuously
- Respect robots.txt

### 5. Document Your Config

```yaml
# This scrapes product listings from Example Shop
# Updated: 2024-01-15
# Maintainer: your-name

name: "Example Shop Products"
description: |
  Scrapes product information including:
  - Product name and description
  - Current and original prices
  - Product images and URLs
  - Available colors

# Rest of config...
```

## Troubleshooting Checklist

When scraping fails:

- [ ] Validate config syntax
- [ ] Test selectors in browser console
- [ ] Check if site requires JavaScript (try `fetcher_type: "browser"`)
- [ ] Verify pagination selectors
- [ ] Check robots.txt
- [ ] Increase timeouts for slow sites
- [ ] Review error messages in output

## Getting Help

If you're stuck:

1. **Check documentation:**
   - [User Guide](USER_GUIDE.md)
   - [Developer Guide](DEV_GUIDE.md)

2. **Test in browser:**
   - Inspect elements
   - Test selectors in console

3. **Ask for help:**
   - GitHub Issues
   - GitHub Discussions

---

Happy scraping! Remember: every website is different, be patient and iterate. 🕷️
