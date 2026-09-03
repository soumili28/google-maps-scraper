"""
Configuration and Centralized Selectors for Google Maps Scraper.
"""

import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


@dataclass(frozen=True)
class DOMSelectors:
    """Centralized DOM selectors for resilient Google Maps scraping."""

    # Consent Dialogs
    CONSENT_BUTTONS: List[str] = field(default_factory=lambda: [
        'form[action*="consent.google.com"] button',
        'button[aria-label*="Accept all"]',
        'button[aria-label*="Tout accepter"]',
        'button[aria-label*="Alle akzeptieren"]',
        'button:has-text("Accept all")',
        'button:has-text("I agree")',
        'button:has-text("Accept")',
        'button:has-text("Agree")',
        'button[jsname="b3Ekab"]',  # Standard Google Agree button jsname
    ])

    # CAPTCHA and Bot Detection
    CAPTCHA_INDICATORS: List[str] = field(default_factory=lambda: [
        'form#captcha-form',
        'div#recaptcha',
        'div.g-recaptcha',
        'iframe[src*="recaptcha"]',
        'iframe[src*="google.com/recaptcha"]',
        '#captcha',
    ])
    CAPTCHA_URL_SIGNATURES: List[str] = field(default_factory=lambda: [
        "/sorry/index",
        "google.com/sorry",
        "recaptcha",
    ])
    CAPTCHA_PAGE_TEXTS: List[str] = field(default_factory=lambda: [
        "unusual traffic from your computer network",
        "please solve this captcha",
        "our systems have detected unusual traffic",
        "verify that you are not a robot",
        "verify you are human",
    ])

    # Feed & Results List
    FEED_CONTAINERS: List[str] = field(default_factory=lambda: [
        'div[role="feed"]',
        'div.m6QErb[aria-label*="Results for"]',
        'div.m6QErb[aria-label*="results"]',
        'div.m6QErb.DxyBCb.kA9KIf.dS8AEf',
        'div.m6QErb',
    ])

    # Feed Item Cards / Links
    LISTING_CARD_LINKS: List[str] = field(default_factory=lambda: [
        'a.hfpxzc',
        'div.Nv2Wy a.hfpxzc',
        'a[href*="/maps/place/"]',
    ])

    LISTING_CONTAINERS: List[str] = field(default_factory=lambda: [
        'div.Nv2Wy',
        'div.bfubId',
        'div[role="article"]',
        'div.m6QErb div.THL2l',
    ])

    # End of Feed Indicator
    END_OF_FEED_INDICATORS: List[str] = field(default_factory=lambda: [
        'div.HlvSq',
        'p.fontBodyMedium:has-text("You\'ve reached the end of the list.")',
        'span:has-text("You\'ve reached the end of the list.")',
        'span:has-text("No more results")',
    ])

    # Single Business Place Pane (when query directly opens one place)
    SINGLE_PLACE_CONTAINER: List[str] = field(default_factory=lambda: [
        'div[role="main"][aria-label]',
        'div.m6QErb.WNBkOb',
    ])

    # Detail Pane Elements
    PLACE_NAME: List[str] = field(default_factory=lambda: [
        'h1.DUwDvf',
        'h1.fontHeadlineLarge',
        'div[role="main"] h1',
        'h1[tabindex="-1"]',
    ])

    RATING: List[str] = field(default_factory=lambda: [
        'span.ceNzKf',
        'div.F7nice span[aria-hidden="true"]',
        'div.F7nice span.ceNzKf',
        'span.fontDisplayLarge',
    ])

    REVIEWS_COUNT: List[str] = field(default_factory=lambda: [
        'div.F7nice',
        'div.F7nice span[aria-label*="review"]',
        'div.F7nice span[aria-label*="Review"]',
        'span[aria-label*="review"]',
        'span[aria-label*="Review"]',
        'button[aria-label*="review"]',
        'div.F7nice button',
        'span.UY7F9',
        'span.ZkP5Je',
    ])

    CATEGORY: List[str] = field(default_factory=lambda: [
        'button.DkEaL',
        'span.fontBodyMedium button.DkEaL',
        'button[jsaction*="category"]',
        'span.mgr77e button',
    ])

    ADDRESS: List[str] = field(default_factory=lambda: [
        'button[data-item-id="address"]',
        'button[aria-label*="Address:"]',
        '[data-item-id="address"] div.fontBodyMedium',
        'button[data-tooltip*="Copy address"]',
    ])

    WEBSITE: List[str] = field(default_factory=lambda: [
        'a[data-item-id="authority"]',
        'a[aria-label*="Website:"]',
        'a[data-tooltip*="Open website"]',
        'a.CsEnBe[href^="http"]',
    ])

    PHONE: List[str] = field(default_factory=lambda: [
        'button[data-item-id^="phone:"]',
        'button[aria-label*="Phone:"]',
        'button[data-tooltip*="Copy phone number"]',
        '[data-item-id^="phone:"] div.fontBodyMedium',
    ])

    STATUS_OR_HOURS: List[str] = field(default_factory=lambda: [
        'button[data-item-id="oh"]',
        'div.t39EBf',
        'div.OM3Cq',
        'span.ZDu9vd',
        'div[aria-label*="Hours"]',
    ])


# Default Settings
DEFAULT_HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
DEFAULT_TIMEOUT_MS = int(os.getenv("TIMEOUT_MS", "30000"))
DEFAULT_PAGE_LOAD_TIMEOUT_MS = int(os.getenv("PAGE_LOAD_TIMEOUT_MS", "45000"))
DEFAULT_MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
DEFAULT_BACKOFF_FACTOR = float(os.getenv("BACKOFF_FACTOR", "2.0"))
DEFAULT_OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEFAULT_USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)
DEFAULT_LOCALE = os.getenv("LOCALE", "en-US")
DEFAULT_VIEWPORT_WIDTH = int(os.getenv("VIEWPORT_WIDTH", "1920"))
DEFAULT_VIEWPORT_HEIGHT = int(os.getenv("VIEWPORT_HEIGHT", "1080"))
DEFAULT_SLOW_MO_MS = int(os.getenv("SLOW_MO_MS", "0"))

SELECTORS = DOMSelectors()
