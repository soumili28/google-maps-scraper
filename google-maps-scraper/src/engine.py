"""
Main scraping engine coordinating browser automation, page state handling,
consent/CAPTCHA detection, feed scrolling, item extraction, and export validation.
"""

import time
import urllib.parse
from typing import List, Optional, Tuple, Set
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator

from src.models import BusinessListing, ScrapeResult, ScraperConfig
from src.config import SELECTORS
from src.exceptions import (
    CaptchaDetectedError,
    ConsentDialogError,
    ScrapingTimeoutError,
)
from src.logger import setup_logger
from src.browser import BrowserManager
from src.parser import (
    parse_rating,
    parse_reviews_count,
    parse_phone_number,
    parse_coordinates_from_url,
    parse_name_from_url,
    clean_address,
    clean_status_or_hours,
    clean_website_url,
    clean_text,
    clean_unicode_icons,
)
from src.exporter import (
    generate_export_paths,
    export_to_csv,
    export_to_xlsx,
    validate_export,
)

logger = setup_logger("scraper.engine")


class GoogleMapsScraper:
    """Production-grade Google Maps scraper with robust error handling and resilient extraction."""

    def __init__(self, config: ScraperConfig):
        self.config = config

    def run(self) -> ScrapeResult:
        """
        Executes the scraping lifecycle:
        1. Launches browser context
        2. Navigates to Google Maps search
        3. Handles consent modals and checks for CAPTCHA/bot challenges
        4. Discovers and scrolls listings feed
        5. Extracts details per listing with per-item isolation
        6. Exports data to styled XLSX and standard CSV
        7. Validates generated files
        """
        start_time = time.time()
        result = ScrapeResult(query=self.config.query)
        logger.info(f"Starting Google Maps scrape for query: '{self.config.query}' (Max results: {self.config.max_results})")

        with BrowserManager.create_page(self.config) as (page, context):
            try:
                # Step 1: Navigate to search query
                self._navigate_with_retry(page, self.config.query)

                # Step 2: Handle consent dialogs if present
                self._handle_consent_dialog(page)

                # Step 3: Check for CAPTCHA / Bot detection
                if self._is_captcha_detected(page):
                    logger.warning("Bot protection / CAPTCHA detected on initial page load. Stopping gracefully.")
                    result.stopped_early = True
                    result.stop_reason = "CAPTCHA or bot-detection page encountered."
                    return self._finalize_result(result, start_time)

                # Step 4: Extract listings
                listings = self._extract_listings(page)
                result.listings = listings
                result.total_found = len(listings)

            except CaptchaDetectedError as cde:
                logger.warning(f"Aborting scrape due to access control: {cde}")
                result.stopped_early = True
                result.stop_reason = str(cde)
            except Exception as e:
                logger.error(f"Unexpected error during scraping: {e}", exc_info=True)
                result.stopped_early = True
                result.stop_reason = f"Error: {e}"

        return self._finalize_result(result, start_time)

    def _navigate_with_retry(self, page: Page, query: str) -> None:
        """Navigates to Google Maps search with exponential backoff."""
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/maps/search/{encoded_query}?hl=en"
        
        attempt = 0
        backoff = 1.0

        while attempt < self.config.max_retries:
            attempt += 1
            try:
                logger.info(f"Navigating to Google Maps (Attempt {attempt}/{self.config.max_retries})...")
                page.goto(search_url, wait_until="domcontentloaded", timeout=self.config.page_load_timeout_ms)
                # Allow dynamic scripts to initialize
                page.wait_for_timeout(2000)
                return
            except PlaywrightTimeoutError as pte:
                logger.warning(f"Navigation timed out on attempt {attempt}: {pte}")
                if attempt >= self.config.max_retries:
                    raise ScrapingTimeoutError(f"Failed to navigate to Google Maps after {self.config.max_retries} attempts.")
                sleep_time = backoff * (self.config.backoff_factor ** (attempt - 1))
                logger.info(f"Retrying navigation in {sleep_time:.1f}s...")
                time.sleep(sleep_time)

    def _handle_consent_dialog(self, page: Page) -> None:
        """Detects and accepts Google's cookie/consent dialog if shown."""
        logger.debug("Checking for Google consent dialog...")
        for selector in SELECTORS.CONSENT_BUTTONS:
            try:
                button = page.locator(selector).first
                if button.is_visible(timeout=1500):
                    logger.info(f"Found consent button matching '{selector}'. Accepting...")
                    button.click()
                    page.wait_for_timeout(2000)
                    return
            except Exception:
                continue

    def _is_captcha_detected(self, page: Page) -> bool:
        """Checks if current page has CAPTCHA, bot detection, or unusual traffic warning."""
        current_url = page.url.lower()

        # 1. URL pattern check
        for signature in SELECTORS.CAPTCHA_URL_SIGNATURES:
            if signature in current_url:
                logger.warning(f"CAPTCHA signature detected in URL: {current_url}")
                return True

        # 2. DOM selector check
        for selector in SELECTORS.CAPTCHA_INDICATORS:
            try:
                elem = page.locator(selector).first
                if elem.is_visible(timeout=500):
                    logger.warning(f"CAPTCHA element found in DOM matching: '{selector}'")
                    return True
            except Exception:
                continue

        # 3. Text content check
        try:
            page_text = page.inner_text("body", timeout=1000).lower()
            for text_pattern in SELECTORS.CAPTCHA_PAGE_TEXTS:
                if text_pattern in page_text:
                    logger.warning(f"CAPTCHA indicator text detected: '{text_pattern}'")
                    return True
        except Exception:
            pass

        return False

    def _find_feed_container(self, page: Page) -> Optional[Locator]:
        """Locates the scrollable feed container on Google Maps."""
        for selector in SELECTORS.FEED_CONTAINERS:
            try:
                locator = page.locator(selector).first
                if locator.is_visible(timeout=2000):
                    logger.debug(f"Identified feed container using selector: '{selector}'")
                    return locator
            except Exception:
                continue
        return None

    def _is_single_place_page(self, page: Page) -> bool:
        """Determines if the search query directly opened a single business detail view."""
        for selector in SELECTORS.SINGLE_PLACE_CONTAINER:
            try:
                locator = page.locator(selector).first
                if locator.is_visible(timeout=1000):
                    # Verify it has a place title and not a generic results header
                    for title_sel in SELECTORS.PLACE_NAME:
                        title_loc = locator.locator(title_sel).first
                        if title_loc.is_visible(timeout=500):
                            text = title_loc.inner_text().strip()
                            if text and not text.lower().startswith("results"):
                                return True
            except Exception:
                continue
        return False

    def _extract_listings(self, page: Page) -> List[BusinessListing]:
        """Scrapes listings by scrolling feed and extracting details for each item."""
        # Check if direct single place page
        if self._is_single_place_page(page):
            logger.info("Direct single place result detected.")
            single_listing = self._extract_single_place_details(page, page.url)
            if single_listing and single_listing.is_valid():
                return [single_listing]
            return []

        # Find feed container
        feed = self._find_feed_container(page)

        listings: List[BusinessListing] = []
        seen_urls: Set[str] = set()

        scroll_attempts = 0
        max_scroll_attempts = 35
        last_item_count = 0
        stagnant_scroll_count = 0

        logger.info(f"Scrolling feed to discover up to {self.config.max_results} listings...")

        while len(seen_urls) < self.config.max_results and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1

            if self._is_captcha_detected(page):
                raise CaptchaDetectedError("CAPTCHA detected during feed scrolling.")

            # Find all card links currently in DOM
            card_links = page.locator(SELECTORS.LISTING_CARD_LINKS[0]).all()
            for link in card_links:
                try:
                    href = link.get_attribute("href") or ""
                    if href and href not in seen_urls and "/maps/place/" in href:
                        seen_urls.add(href)
                except Exception:
                    continue

            logger.debug(f"Scroll iteration {scroll_attempts}: Found {len(seen_urls)} unique place URLs so far.")

            if len(seen_urls) >= self.config.max_results:
                break

            # Check if feed reached the end
            if self._is_end_of_feed(page):
                logger.info("Reached end of Google Maps feed.")
                break

            # Scroll feed down
            if feed:
                try:
                    feed.evaluate("el => el.scrollTop = el.scrollHeight")
                except Exception:
                    page.mouse.wheel(0, 1500)
            else:
                page.mouse.wheel(0, 1500)

            page.wait_for_timeout(1500)

            if len(seen_urls) == last_item_count:
                stagnant_scroll_count += 1
                if stagnant_scroll_count >= 5:
                    logger.info("No new items loading after multiple scroll attempts. Stopping scroll.")
                    break
            else:
                stagnant_scroll_count = 0
                last_item_count = len(seen_urls)

        # Now extract item by item
        card_links = page.locator(SELECTORS.LISTING_CARD_LINKS[0]).all()
        target_count = min(len(card_links), self.config.max_results)
        logger.info(f"Beginning detail extraction for {target_count} listings...")

        for idx in range(target_count):
            try:
                card = card_links[idx]
                listing = self._extract_listing_item(page, card, idx + 1, target_count)
                if listing and listing.is_valid():
                    listings.append(listing)
                    logger.info(
                        f"[{len(listings)}/{target_count}] Extracted: {listing.name} "
                        f"(Rating: {listing.rating or 'N/A'}, Reviews: {listing.reviews_count or 'N/A'}, Phone: {listing.phone or 'N/A'})"
                    )
                else:
                    logger.warning(f"Item #{idx + 1} produced empty or invalid listing. Skipping.")
            except Exception as e:
                # Comprehensive error handling: one malformed listing never terminates scrape!
                logger.error(f"Error extracting listing #{idx + 1}: {e}. Continuing with next item...")
                continue

        return listings

    def _is_end_of_feed(self, page: Page) -> bool:
        """Checks if end-of-results message is visible."""
        for selector in SELECTORS.END_OF_FEED_INDICATORS:
            try:
                elem = page.locator(selector).first
                if elem.is_visible(timeout=300):
                    return True
            except Exception:
                continue
        return False

    def _extract_listing_item(self, page: Page, card: Locator, index: int, total: int) -> Optional[BusinessListing]:
        """Extracts data for a single listing card with synchronization and fallback parsing."""
        try:
            place_url = card.get_attribute("href") or ""
            card_title = card.get_attribute("aria-label") or ""
        except Exception:
            place_url = ""
            card_title = ""

        # Fallback name from URL if aria-label is missing
        if not card_title and place_url:
            card_title = parse_name_from_url(place_url) or ""

        # Coordinates from place_url (prioritizes exact !3d... !4d... over search viewport)
        lat, lng = parse_coordinates_from_url(place_url)

        # Snippet fallback extraction from the feed card container itself
        snippet_rating = None
        snippet_reviews = None
        try:
            card_container = card.locator("xpath=ancestor::div[contains(@class, 'Nv2Wy') or contains(@class, 'bfubId') or contains(@class, 'THL2l')][1]").first
            if card_container.is_visible(timeout=500):
                snippet_rating_text = card_container.locator("span.MW4etd").first.inner_text(timeout=300)
                snippet_rating = parse_rating(snippet_rating_text)
                snippet_reviews_text = card_container.locator("span.UY7F9").first.inner_text(timeout=300)
                snippet_reviews = parse_reviews_count(snippet_reviews_text)
        except Exception:
            pass

        # Click on card to open detail pane
        clicked = False
        try:
            card.scroll_into_view_if_needed(timeout=2000)
            card.click(force=True, timeout=3000)
            clicked = True
            # Allow detail pane transition to complete
            page.wait_for_timeout(2000)
        except Exception as e:
            logger.debug(f"Could not click card #{index} for detail pane: {e}")

        # Synchronize Business Name with detail pane header
        name = clean_unicode_icons(card_title) or card_title
        pane_active = False

        if clicked:
            for name_sel in SELECTORS.PLACE_NAME:
                try:
                    elem = page.locator(name_sel).first
                    if elem.is_visible(timeout=1000):
                        txt = elem.inner_text().strip()
                        if txt and not txt.lower().startswith("results"):
                            # Confirm pane matches this card (prevent reading stale previous card pane)
                            if not card_title or (
                                card_title.lower() in txt.lower() or 
                                txt.lower() in card_title.lower() or
                                any(word.lower() in txt.lower() for word in card_title.split() if len(word) > 3)
                            ):
                                name = clean_unicode_icons(txt) or txt
                                pane_active = True
                                break
                except Exception:
                    continue

        if not name:
            return None

        # Rating & Reviews
        rating = None
        reviews_count = None

        if pane_active:
            # Try detail pane rating
            rating_raw = self._extract_field_with_selectors(page, SELECTORS.RATING)
            rating = parse_rating(rating_raw)

            # Try detail pane reviews
            reviews_raw = self._extract_field_with_selectors(page, SELECTORS.REVIEWS_COUNT)
            reviews_count = parse_reviews_count(reviews_raw)

        # Fallback to card snippet rating / reviews if detail pane was missing them
        if rating is None:
            rating = snippet_rating
        if reviews_count is None:
            reviews_count = snippet_reviews

        # Detail fields (only extract from detail pane if actively synchronized)
        category = None
        address = None
        phone = None
        website = None
        status_or_hours = None

        if pane_active:
            category_raw = self._extract_field_with_selectors(page, SELECTORS.CATEGORY)
            category = clean_unicode_icons(category_raw)

            address_raw = self._extract_field_with_selectors(page, SELECTORS.ADDRESS)
            address = clean_address(address_raw)

            phone_raw = self._extract_field_with_selectors(page, SELECTORS.PHONE)
            phone = parse_phone_number(phone_raw)

            website_raw = self._extract_attr_with_selectors(page, SELECTORS.WEBSITE, "href")
            website = clean_website_url(website_raw)

            status_raw = self._extract_field_with_selectors(page, SELECTORS.STATUS_OR_HOURS)
            status_or_hours = clean_status_or_hours(status_raw)

        # If lat/lng wasn't found in place_url, check current page URL
        if lat is None or lng is None:
            lat, lng = parse_coordinates_from_url(page.url)

        return BusinessListing(
            name=name.strip(),
            rating=rating,
            reviews_count=reviews_count,
            category=category,
            address=address,
            phone=phone,
            website=website,
            place_url=place_url or page.url,
            latitude=lat,
            longitude=lng,
            status_or_hours=status_or_hours,
        )

    def _extract_single_place_details(self, page: Page, current_url: str) -> Optional[BusinessListing]:
        """Extracts listing details when search directly renders a single place."""
        name = self._extract_field_with_selectors(page, SELECTORS.PLACE_NAME)
        if not name or name.lower().startswith("results"):
            name = parse_name_from_url(current_url)

        if not name:
            return None

        rating_raw = self._extract_field_with_selectors(page, SELECTORS.RATING)
        rating = parse_rating(rating_raw)

        reviews_raw = self._extract_field_with_selectors(page, SELECTORS.REVIEWS_COUNT)
        reviews_count = parse_reviews_count(reviews_raw)

        category = clean_unicode_icons(self._extract_field_with_selectors(page, SELECTORS.CATEGORY))
        address = clean_address(self._extract_field_with_selectors(page, SELECTORS.ADDRESS))
        phone = parse_phone_number(self._extract_field_with_selectors(page, SELECTORS.PHONE))
        website = clean_website_url(self._extract_attr_with_selectors(page, SELECTORS.WEBSITE, "href"))

        lat, lng = parse_coordinates_from_url(current_url)
        status_or_hours = clean_status_or_hours(self._extract_field_with_selectors(page, SELECTORS.STATUS_OR_HOURS))

        return BusinessListing(
            name=clean_unicode_icons(name) or name.strip(),
            rating=rating,
            reviews_count=reviews_count,
            category=category,
            address=address,
            phone=phone,
            website=website,
            place_url=current_url,
            latitude=lat,
            longitude=lng,
            status_or_hours=status_or_hours,
        )

    def _extract_field_with_selectors(self, page: Page, selectors: List[str]) -> Optional[str]:
        """Tries multiple selectors sequentially to extract inner text or aria-label."""
        for selector in selectors:
            try:
                elem = page.locator(selector).first
                if elem.is_visible(timeout=600):
                    text = elem.inner_text().strip()
                    if text:
                        return text
                    aria = elem.get_attribute("aria-label")
                    if aria and aria.strip():
                        return aria.strip()
            except Exception:
                continue
        return None

    def _extract_attr_with_selectors(self, page: Page, selectors: List[str], attr_name: str) -> Optional[str]:
        """Tries multiple selectors sequentially to extract an HTML attribute."""
        for selector in selectors:
            try:
                elem = page.locator(selector).first
                if elem.is_visible(timeout=600):
                    val = elem.get_attribute(attr_name)
                    if val and val.strip():
                        return val.strip()
            except Exception:
                continue
        return None

    def _finalize_result(self, result: ScrapeResult, start_time: float) -> ScrapeResult:
        """Exports listings to CSV and XLSX, validates output files, and records duration."""
        result.duration_seconds = time.time() - start_time

        if not result.listings:
            logger.warning("No listings were extracted. Skipping file export.")
            return result

        # Generate paths
        csv_path, xlsx_path = generate_export_paths(self.config.query, self.config.output_dir)

        # Export CSV
        export_to_csv(result.listings, csv_path)
        result.csv_path = csv_path
        logger.info(f"CSV successfully written to: {csv_path}")

        # Export XLSX
        export_to_xlsx(result.listings, xlsx_path)
        result.xlsx_path = xlsx_path
        logger.info(f"Excel XLSX successfully written to: {xlsx_path}")

        # Validate Exports
        try:
            csv_val = validate_export(csv_path, len(result.listings))
            xlsx_val = validate_export(xlsx_path, len(result.listings))
            result.validated = True
            logger.info(f"Export Validation Passed for CSV: {csv_val['record_count']} records verified ({csv_val['file_size_bytes']} bytes).")
            logger.info(f"Export Validation Passed for XLSX: {xlsx_val['record_count']} records verified ({xlsx_val['file_size_bytes']} bytes).")
        except Exception as e:
            logger.error(f"Post-export validation failed: {e}")
            result.validated = False

        return result
