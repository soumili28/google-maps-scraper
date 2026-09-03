"""
DOM Parsing, data extraction, and regex normalization utilities for Google Maps.
"""

import re
import urllib.parse
from typing import Optional, Tuple, List, Union


def clean_unicode_icons(text: Optional[str]) -> Optional[str]:
    """
    Strips private-use unicode icon characters (e.g. \ue0b0, \ue0c8, \ue8b5)
    and non-standard control characters commonly found in Google Maps DOM.
    """
    if not text:
        return None
    # Remove private-use unicode block \uE000-\uF8FF and common control chars
    cleaned = re.sub(r"[\ue000-\uf8ff\ufffd]", "", text)
    # Remove zero-width spaces
    cleaned = cleaned.replace("\u200b", "").replace("\ufeff", "")
    return clean_text(cleaned)


def parse_rating(text: Optional[str]) -> Optional[float]:
    """
    Extracts a numeric float rating from text or aria-label (e.g. '4.8', '4.8 stars', '4,9 of 5').
    """
    if not text:
        return None
    
    # Replace comma with period for European locale decimals
    cleaned = text.replace(",", ".")
    # Match first floating-point or integer number in string
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", cleaned)
    if match:
        try:
            val = float(match.group(1))
            if 1.0 <= val <= 5.0:
                return round(val, 1)
        except ValueError:
            pass
    return None


def parse_reviews_count(text: Optional[str]) -> Optional[int]:
    """
    Extracts review count integer from text (e.g. '(1,234)', '4.9 (843)', '1,234 reviews', '56 reviews', '1.2K reviews').
    """
    if not text:
        return None
    
    cleaned = clean_unicode_icons(text) or text
    cleaned_lower = cleaned.lower()

    # Pattern 1: Count inside parentheses e.g. (1,234) or 4.9 (843)
    paren_match = re.search(r"\(([\d,]+(?:\.\d+)?k?)\)", cleaned_lower)
    if paren_match:
        inner = paren_match.group(1).replace(",", "")
        if "k" in inner:
            try:
                return int(float(inner.replace("k", "")) * 1000)
            except ValueError:
                pass
        else:
            try:
                return int(inner)
            except ValueError:
                pass

    # Pattern 2: '1.2k' or '2.5m' notation
    k_match = re.search(r"(\d+(?:\.\d+)?)\s*k\b", cleaned_lower)
    if k_match:
        try:
            return int(float(k_match.group(1)) * 1000)
        except ValueError:
            pass

    # Pattern 3: explicit 'reviews' e.g. "843 reviews"
    rev_match = re.search(r"([\d,]+)\s+review", cleaned_lower)
    if rev_match:
        try:
            return int(rev_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Pattern 4: General digits if string doesn't contain decimal rating alone
    # Avoid picking up decimal rating if text is only '4.9'
    digits_only = re.sub(r"[^\d]", "", cleaned_lower)
    if digits_only and not re.match(r"^[1-5]\d$", digits_only):  # Not just '49' from '4.9'
        try:
            return int(digits_only)
        except ValueError:
            pass

    return None


def parse_phone_number(text: Optional[str]) -> Optional[str]:
    """
    Cleans and standardizes raw phone strings.
    """
    if not text:
        return None
    # Strip unicode icons first
    cleaned = clean_unicode_icons(text)
    if not cleaned:
        return None
    # Strip common prefixes
    cleaned = re.sub(r"^(phone|tel|call):\s*", "", cleaned, flags=re.IGNORECASE)
    # Remove excessive whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else None


def parse_coordinates_from_url(url: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts latitude and longitude from Google Maps URLs.
    Prioritizes exact place data coordinates (!3d... !4d...) over viewport center coordinates (/@...).
    """
    if not url:
        return None, None

    # Priority 1: Exact Place coordinates !3d<lat>!4d<lng>
    match_d = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
    if match_d:
        try:
            return float(match_d.group(1)), float(match_d.group(2))
        except ValueError:
            pass

    # Priority 2: Viewport /@lat,lng,
    match_at = re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", url)
    if match_at:
        try:
            return float(match_at.group(1)), float(match_at.group(2))
        except ValueError:
            pass

    return None, None


def parse_name_from_url(url: Optional[str]) -> Optional[str]:
    """
    Extracts business name encoded in a Google Maps URL path /maps/place/<Name>/...
    """
    if not url:
        return None
    match = re.search(r"/maps/place/([^/@?]+)", url)
    if match:
        raw_name = match.group(1).replace("+", " ")
        return urllib.parse.unquote(raw_name).strip()
    return None


def clean_address(raw_address: Optional[str]) -> Optional[str]:
    """Cleans raw address string, stripping leading 'Address:' and unicode icons."""
    if not raw_address:
        return None
    cleaned = clean_unicode_icons(raw_address)
    if not cleaned:
        return None
    if cleaned.lower().startswith("address:"):
        cleaned = cleaned[8:].strip()
    return cleaned if cleaned else None


def clean_status_or_hours(raw_text: Optional[str]) -> Optional[str]:
    """Cleans hours and status string, removing trailing 'See more hours' and icons."""
    if not raw_text:
        return None
    cleaned = clean_unicode_icons(raw_text)
    if not cleaned:
        return None
    # Remove 'See more hours' or extra UI action text
    cleaned = re.sub(r"(?i)\bsee\s+more\s+hours\b", "", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else None


def clean_website_url(raw_url: Optional[str]) -> Optional[str]:
    """
    Unwraps Google redirect URLs and returns clean canonical destination URL.
    """
    if not raw_url:
        return None
    raw_url = raw_url.strip()
    
    # Handle google.com/url?q=... redirects
    if "google.com/url?" in raw_url:
        match = re.search(r"[?&]q=([^&]+)", raw_url)
        if match:
            return urllib.parse.unquote(match.group(1))
            
    return raw_url


def clean_text(raw_text: Optional[str]) -> Optional[str]:
    """Cleans general text strings, removing extra spaces and newlines."""
    if not raw_text:
        return None
    cleaned = " ".join(raw_text.strip().split())
    return cleaned if cleaned else None
