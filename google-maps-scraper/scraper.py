"""
Google Maps Scraper - CLI Entry Point.

Usage:
    python scraper.py --query "Dentists in Austin, TX" --max-results 10
    python scraper.py --query "Coffee shops in Seattle" --max-results 20 --headless
    python scraper.py -q "Restaurants in Chicago" -m 5 --no-headless
"""

import sys
import argparse
from src.models import ScraperConfig, ScrapeResult
from src.engine import GoogleMapsScraper
from src.logger import setup_logger
from src.config import (
    DEFAULT_HEADLESS,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_LOG_LEVEL,
    DEFAULT_TIMEOUT_MS,
    DEFAULT_PAGE_LOAD_TIMEOUT_MS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BACKOFF_FACTOR,
)


def build_parser() -> argparse.ArgumentParser:
    """Builds and returns the command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="google-maps-scraper",
        description="Production-Grade Google Maps Business Leads Scraper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-q", "--query",
        type=str,
        required=True,
        help="Search query to execute on Google Maps (e.g. 'Dentists in Austin, TX')",
    )

    parser.add_argument(
        "-m", "--max-results",
        type=int,
        default=10,
        help="Maximum number of business listings to scrape",
    )

    # Headless toggle
    parser.add_argument(
        "--headless",
        action=argparse.BooleanOptionalAction,
        default=DEFAULT_HEADLESS,
        help="Run browser in headless mode (--headless or --no-headless)",
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where CSV and XLSX outputs will be saved",
    )

    parser.add_argument(
        "-l", "--log-level",
        type=str,
        default=DEFAULT_LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity level",
    )

    return parser


def main() -> int:
    """CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    # Initialize Logger
    logger = setup_logger("scraper", level=args.log_level)
    logger.info("=" * 60)
    logger.info("Google Maps Production Scraper Initialized")
    logger.info(f"Query       : {args.query}")
    logger.info(f"Max Results : {args.max_results}")
    logger.info(f"Headless    : {args.headless}")
    logger.info(f"Output Dir  : {args.output_dir}")
    logger.info(f"Log Level   : {args.log_level}")
    logger.info("=" * 60)

    config = ScraperConfig(
        query=args.query,
        max_results=args.max_results,
        headless=args.headless,
        output_dir=args.output_dir,
        log_level=args.log_level,
        timeout_ms=DEFAULT_TIMEOUT_MS,
        page_load_timeout_ms=DEFAULT_PAGE_LOAD_TIMEOUT_MS,
        max_retries=DEFAULT_MAX_RETRIES,
        backoff_factor=DEFAULT_BACKOFF_FACTOR,
    )

    scraper = GoogleMapsScraper(config)
    result: ScrapeResult = scraper.run()

    # Print Final Summary
    print("\n" + "=" * 60)
    print("SCRAPE RUN SUMMARY")
    print("=" * 60)
    print(f"Search Query        : {result.query}")
    print(f"Total Extracted     : {result.total_found}")
    print(f"Execution Duration  : {result.duration_seconds:.2f}s")
    print(f"Stopped Early       : {result.stopped_early} ({result.stop_reason or 'Completed'})")
    print(f"Validation Status   : {'PASSED' if result.validated else 'SKIPPED/FAILED'}")
    if result.csv_path:
        print(f"CSV Export File     : {result.csv_path}")
    if result.xlsx_path:
        print(f"XLSX Export File    : {result.xlsx_path}")
    print("=" * 60 + "\n")

    if result.total_found > 0 and result.validated:
        return 0
    elif result.total_found > 0:
        return 0
    elif result.stopped_early:
        logger.warning(f"Run terminated early: {result.stop_reason}")
        return 0
    else:
        logger.error("No results could be extracted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
