"""Tests for parsing, sanitizing, and regex extraction functions."""

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


def test_parse_rating():
    assert parse_rating("4.8") == 4.8
    assert parse_rating("4.8 stars") == 4.8
    assert parse_rating("4,9 of 5 stars") == 4.9
    assert parse_rating("5.0") == 5.0
    assert parse_rating("3") == 3.0
    assert parse_rating("No reviews") is None
    assert parse_rating("") is None
    assert parse_rating(None) is None
    assert parse_rating("6.5") is None  # Out of valid rating bounds


def test_parse_reviews_count():
    assert parse_reviews_count("(1,234)") == 1234
    assert parse_reviews_count("1,234 reviews") == 1234
    assert parse_reviews_count("56 reviews") == 56
    assert parse_reviews_count("1.2k reviews") == 1200
    assert parse_reviews_count("2.5K") == 2500
    assert parse_reviews_count("No reviews yet") is None
    assert parse_reviews_count("") is None
    assert parse_reviews_count(None) is None


def test_parse_phone_number():
    assert parse_phone_number("Phone: +1 512-555-0199") == "+1 512-555-0199"
    assert parse_phone_number("Tel: (512) 555-0199") == "(512) 555-0199"
    assert parse_phone_number("  512-555-0199   ") == "512-555-0199"
    assert parse_phone_number("\ue0b0 +1 512-555-0199") == "+1 512-555-0199"
    assert parse_phone_number("") is None
    assert parse_phone_number(None) is None


def test_parse_coordinates_from_url():
    url1 = "https://www.google.com/maps/place/Austin+Dental/@30.267153,-97.7430608,17z/data=!3m1!4b1"
    lat1, lng1 = parse_coordinates_from_url(url1)
    assert lat1 == 30.267153
    assert lng1 == -97.7430608

    url2 = "https://www.google.com/maps/search/dentists/!3d30.3406789!4d-97.6924276"
    lat2, lng2 = parse_coordinates_from_url(url2)
    assert lat2 == 30.3406789
    assert lng2 == -97.6924276

    url_empty = "https://www.google.com/maps"
    lat3, lng3 = parse_coordinates_from_url(url_empty)
    assert lat3 is None
    assert lng3 is None


def test_parse_name_from_url():
    url = "https://www.google.com/maps/place/Austin+Lifetime+Dental/data=!4m7!3m6!1s0x8644cc20724ee6f5"
    assert parse_name_from_url(url) == "Austin Lifetime Dental"

    url2 = "https://www.google.com/maps/place/Emergency+Dentist+of+Austin/@30.34,-97.69"
    assert parse_name_from_url(url2) == "Emergency Dentist of Austin"

    assert parse_name_from_url("https://www.google.com/maps") is None


def test_clean_address():
    raw = "\ue0c8 2206 W Parmer Ln, Austin, TX 78727"
    assert clean_address(raw) == "2206 W Parmer Ln, Austin, TX 78727"

    raw2 = "Address: 123 Main St, Austin, TX"
    assert clean_address(raw2) == "123 Main St, Austin, TX"


def test_clean_status_or_hours():
    raw = "\ue8b5 Closed \u00b7 Opens 7:30 am Mon \n See more hours \n \ue5cc"
    cleaned = clean_status_or_hours(raw)
    assert "Closed" in cleaned
    assert "See more hours" not in cleaned


def test_clean_website_url():
    raw1 = "https://www.google.com/url?q=https://austindental.example.com/contact&sa=U"
    assert clean_website_url(raw1) == "https://austindental.example.com/contact"

    raw2 = "https://austindental.example.com"
    assert clean_website_url(raw2) == "https://austindental.example.com"

    assert clean_website_url("") is None
    assert clean_website_url(None) is None


def test_clean_text_and_unicode():
    assert clean_text("  Austin   Dental   Group \n ") == "Austin Dental Group"
    assert clean_unicode_icons("\ue0b0 Tech Ridge Dental \ue8b5") == "Tech Ridge Dental"
