# Google Maps Scraper (Production-Grade Lead Generation)

A resilient, production-ready Python scraping application for extracting business listings and contact data from Google Maps. Built with Playwright, OpenPyXL, and structured error-handling architectures.

---

## Features

- **Robust Browser Automation**: Powered by Playwright Chromium with anti-bot headers, custom user-agent spoofing, and clean lifecycle management.
- **Graceful Consent & Bot Detection**:
  - Automatically handles Google cookie and consent prompts across locales.
  - Detects CAPTCHA and unusual traffic protection pages; stops gracefully and reports the issue without attempting unauthorized bypass.
- **Resilient Multi-Tier DOM Parsing**:
  - Centralized selector configuration with fallback chains for dynamic Google Maps classes.
  - Per-item error isolation: Malformed or missing fields in one listing will never terminate the scrape run.
- **Exponential Backoff Retries**: Configurable exponential retry strategy for network hiccups and dynamic DOM loading.
- **Rich Excel (.xlsx) & CSV Exports**:
  - Formatted navy headers, bold white text, and auto-filters.
  - Frozen header panes (`A2`).
  - Auto-fitted column widths and multi-line text wrapping for addresses and categories.
  - Clickable active hyperlinks for **Website URL** and **Google Maps Place URL**.
- **Post-Export Validation**:
  - Automatically verifies output file existence, non-zero file sizes, readability, and exact record counts.
- **CLI Interface**: Flexible command-line options via standard `argparse`.

---

## Project Structure

```
google-maps-scraper/
│
├── src/
│   ├── __init__.py        # Package initialization
│   ├── browser.py         # Playwright browser manager & stealth context
│   ├── config.py          # Centralized DOM selectors & environment settings
│   ├── engine.py          # Core scraping orchestrator (navigation, scrolling, extraction)
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── exporter.py        # CSV & OpenPyXL styled export with validation
│   ├── logger.py          # Structured logging setup
│   ├── models.py          # Dataclasses (BusinessListing, ScraperConfig, ScrapeResult)
│   └── parser.py          # Parsing, regex extractors, and data sanitization
│
├── tests/
│   ├── __init__.py
│   ├── test_config.py     # Configuration and CLI parser tests
│   ├── test_exporter.py   # Excel/CSV formatting and validation tests
│   ├── test_models.py     # Dataclass serialization tests
│   └── test_parser.py     # Parser regex & string cleaning tests
│
├── output/                # Destination directory for CSV and XLSX files
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore patterns
├── requirements.txt       # Python dependencies
├── scraper.py             # CLI Entrypoint
└── README.md              # Project documentation
```

---

## Installation

### 1. Prerequisites
- Python 3.10+
- `pip`

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
python -m playwright install chromium
```

---

## Configuration

Copy `.env.example` to `.env` (optional):
```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `HEADLESS` | `true` | Run browser in headless mode (`true`/`false`) |
| `TIMEOUT_MS` | `30000` | General locator timeout in milliseconds |
| `PAGE_LOAD_TIMEOUT_MS` | `45000` | Page navigation timeout in milliseconds |
| `MAX_RETRIES` | `3` | Maximum navigation retry attempts |
| `BACKOFF_FACTOR` | `2.0` | Multiplier for exponential backoff delay |
| `OUTPUT_DIR` | `output` | Directory for exported files |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## CLI Usage

### Basic Search
```bash
python scraper.py --query "Dentists in Austin, TX" --max-results 10
```

### Options & Flags
```bash
python scraper.py [OPTIONS]

Options:
  -q, --query TEXT            Search query on Google Maps (Required)
  -m, --max-results INT       Maximum listings to scrape (Default: 10)
  --headless / --no-headless  Toggle browser UI visibility (Default: headless)
  -o, --output-dir PATH       Destination output directory (Default: output)
  -l, --log-level LEVEL       Log level: DEBUG, INFO, WARNING, ERROR (Default: INFO)
  -h, --help                  Show help message and exit
```

### Examples
```bash
# Visible browser window for debugging
python scraper.py -q "Coffee shops in Seattle" -m 15 --no-headless

# Verbose debug logging with custom output folder
python scraper.py -q "Plumbers in Chicago" -m 25 -o my_leads -l DEBUG
```

---

## Extracted Data Fields

Each listing contains the following attributes:

1. **Name**: Business name
2. **Rating**: Average star rating (1.0 - 5.0)
3. **Reviews Count**: Total number of user reviews
4. **Category**: Primary business category
5. **Address**: Full physical address
6. **Phone**: Standardized contact telephone number
7. **Website**: Clean destination website URL (hyperlinked in Excel)
8. **Google Maps URL**: Direct Place URL (hyperlinked in Excel)
9. **Latitude & Longitude**: Geocoordinates extracted from Map state
10. **Status / Hours**: Current operating hours or open status
11. **Scraped At (UTC)**: ISO 8601 UTC timestamp of extraction

---

## Running Tests

Run the automated test suite with `pytest`:
```bash
python -m pytest tests/ -v
```

---

## Ethical Scraping & Rate Limits

- This tool operates with respect to web standards and rate limits.
- If Google presents a CAPTCHA or bot verification wall, the scraper **halts gracefully** without attempting bypass or evasion, ensuring compliance with network access boundaries.
