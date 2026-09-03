"""Tests for configuration and CLI argument parsing."""

from src.config import SELECTORS, DOMSelectors, DEFAULT_MAX_RETRIES
from scraper import build_parser


def test_dom_selectors_integrity():
    assert len(SELECTORS.CONSENT_BUTTONS) > 0
    assert len(SELECTORS.CAPTCHA_INDICATORS) > 0
    assert len(SELECTORS.FEED_CONTAINERS) > 0
    assert len(SELECTORS.LISTING_CARD_LINKS) > 0
    assert len(SELECTORS.PLACE_NAME) > 0
    assert len(SELECTORS.WEBSITE) > 0


def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--query", "Dentists in Austin, TX"])
    assert args.query == "Dentists in Austin, TX"
    assert args.max_results == 10
    assert args.headless is True
    assert args.output_dir == "output"
    assert args.log_level == "INFO"


def test_cli_parser_custom_args():
    parser = build_parser()
    args = parser.parse_args([
        "-q", "Bakeries in Paris",
        "-m", "25",
        "--no-headless",
        "-o", "custom_output",
        "-l", "DEBUG",
    ])
    assert args.query == "Bakeries in Paris"
    assert args.max_results == 25
    assert args.headless is False
    assert args.output_dir == "custom_output"
    assert args.log_level == "DEBUG"
