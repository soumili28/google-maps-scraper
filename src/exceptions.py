"""
Custom exceptions for the Google Maps Scraper.
"""


class ScraperException(Exception):
    """Base exception for all scraper-related errors."""
    pass


class CaptchaDetectedError(ScraperException):
    """Raised when CAPTCHA, bot detection, or unusual traffic block is encountered."""
    def __init__(self, message: str = "CAPTCHA or bot-detection page encountered. Stopping gracefully."):
        super().__init__(message)


class ConsentDialogError(ScraperException):
    """Raised when Google consent dialog cannot be handled or bypassed."""
    pass


class ScrapingTimeoutError(ScraperException):
    """Raised when a scraping operation exceeds timeout limits after retries."""
    pass


class ExtractionError(ScraperException):
    """Raised when critical DOM extraction fails."""
    pass


class ExportValidationError(ScraperException):
    """Raised when exported file fails post-export validation."""
    pass
