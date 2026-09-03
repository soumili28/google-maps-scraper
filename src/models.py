"""
Data models and schemas for Google Maps Scraper.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


@dataclass
class BusinessListing:
    """Represents an individual business listing scraped from Google Maps."""

    name: str
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    category: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    place_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status_or_hours: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert listing to a clean dictionary representation."""
        return {
            "name": self.name or "",
            "rating": self.rating if self.rating is not None else "",
            "reviews_count": self.reviews_count if self.reviews_count is not None else "",
            "category": self.category or "",
            "address": self.address or "",
            "phone": self.phone or "",
            "website": self.website or "",
            "place_url": self.place_url or "",
            "latitude": self.latitude if self.latitude is not None else "",
            "longitude": self.longitude if self.longitude is not None else "",
            "status_or_hours": self.status_or_hours or "",
            "scraped_at": self.scraped_at,
        }

    def is_valid(self) -> bool:
        """A listing is considered valid if it has at least a business name."""
        return bool(self.name and self.name.strip())


@dataclass
class ScraperConfig:
    """Runtime configuration for scraper execution."""

    query: str
    max_results: int = 10
    headless: bool = True
    output_dir: str = "output"
    timeout_ms: int = 30000
    page_load_timeout_ms: int = 45000
    max_retries: int = 3
    backoff_factor: float = 2.0
    slow_mo_ms: int = 0
    log_level: str = "INFO"
    user_agent: Optional[str] = None
    locale: str = "en-US"
    viewport_width: int = 1920
    viewport_height: int = 1080


@dataclass
class ScrapeResult:
    """Aggregate result from a scraping session."""

    query: str
    total_found: int = 0
    listings: List[BusinessListing] = field(default_factory=list)
    csv_path: Optional[str] = None
    xlsx_path: Optional[str] = None
    duration_seconds: float = 0.0
    stopped_early: bool = False
    stop_reason: Optional[str] = None
    validated: bool = False

    def to_summary_dict(self) -> Dict[str, Any]:
        """Return high-level summary of scraping results."""
        return {
            "query": self.query,
            "total_found": self.total_found,
            "csv_path": self.csv_path,
            "xlsx_path": self.xlsx_path,
            "duration_seconds": round(self.duration_seconds, 2),
            "stopped_early": self.stopped_early,
            "stop_reason": self.stop_reason,
            "validated": self.validated,
        }
