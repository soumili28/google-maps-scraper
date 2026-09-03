"""Tests for data models."""

from src.models import BusinessListing, ScrapeResult, ScraperConfig


def test_business_listing_defaults_and_validation():
    listing = BusinessListing(name="Austin Family Dental")
    assert listing.name == "Austin Family Dental"
    assert listing.is_valid() is True
    assert listing.rating is None
    assert listing.reviews_count is None
    assert listing.scraped_at is not None

    invalid_listing = BusinessListing(name="")
    assert invalid_listing.is_valid() is False


def test_business_listing_to_dict():
    listing = BusinessListing(
        name="Texas Dental Care",
        rating=4.9,
        reviews_count=250,
        category="Dentist",
        address="123 Congress Ave, Austin, TX",
        phone="+1 512-555-0199",
        website="https://texasdentalcare.example.com",
        place_url="https://maps.google.com/?cid=12345",
        latitude=30.2672,
        longitude=-97.7431,
        status_or_hours="Open ⋅ Closes 5 PM",
    )
    d = listing.to_dict()
    assert d["name"] == "Texas Dental Care"
    assert d["rating"] == 4.9
    assert d["reviews_count"] == 250
    assert d["category"] == "Dentist"
    assert d["address"] == "123 Congress Ave, Austin, TX"
    assert d["phone"] == "+1 512-555-0199"
    assert d["website"] == "https://texasdentalcare.example.com"
    assert d["latitude"] == 30.2672
    assert d["longitude"] == -97.7431
    assert d["status_or_hours"] == "Open ⋅ Closes 5 PM"


def test_scrape_result_summary():
    result = ScrapeResult(
        query="Dentists in Austin, TX",
        total_found=5,
        csv_path="output/test.csv",
        xlsx_path="output/test.xlsx",
        duration_seconds=12.345,
        validated=True,
    )
    summary = result.to_summary_dict()
    assert summary["query"] == "Dentists in Austin, TX"
    assert summary["total_found"] == 5
    assert summary["duration_seconds"] == 12.35
    assert summary["validated"] is True
