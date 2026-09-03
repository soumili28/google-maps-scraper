"""
Browser lifecycle and Playwright context manager.
"""

from contextlib import contextmanager
from typing import Generator, Tuple
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

from src.models import ScraperConfig
from src.logger import setup_logger

logger = setup_logger("scraper.browser")


class BrowserManager:
    """Manages Playwright browser initialization and anti-detection settings."""

    @staticmethod
    @contextmanager
    def create_page(config: ScraperConfig) -> Generator[Tuple[Page, BrowserContext], None, None]:
        """
        Context manager that launches a Chromium browser with production-ready
        stealth and anti-detection configurations, yielding (Page, BrowserContext).
        Ensures all browser resources are terminated safely upon exit.
        """
        logger.debug("Initializing Playwright engine...")
        with sync_playwright() as p:
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
            ]

            browser: Browser = p.chromium.launch(
                headless=config.headless,
                slow_mo=config.slow_mo_ms,
                args=launch_args,
            )

            context: BrowserContext = browser.new_context(
                user_agent=config.user_agent,
                locale=config.locale,
                timezone_id="America/Chicago",
                viewport={"width": config.viewport_width, "height": config.viewport_height},
                device_scale_factor=1.0,
                has_touch=False,
                is_mobile=False,
                permissions=["geolocation"],
            )

            # Prevent webdriver flag detection
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page: Page = context.new_page()
            page.set_default_timeout(config.timeout_ms)
            page.set_default_navigation_timeout(config.page_load_timeout_ms)

            try:
                yield page, context
            finally:
                logger.debug("Tearing down browser context and page...")
                try:
                    page.close()
                except Exception:
                    pass
                try:
                    context.close()
                except Exception:
                    pass
                try:
                    browser.close()
                except Exception:
                    pass
