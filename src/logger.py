"""
Structured logging module for the scraper with safe unicode encoding support.
"""

import io
import logging
import sys
from typing import Optional


class SafeStreamHandler(logging.StreamHandler):
    """A StreamHandler that gracefully handles non-encodable console characters."""

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                # Encode with replacement character for terminals with limited codepages (e.g. cp1252)
                encoding = getattr(stream, "encoding", "utf-8") or "utf-8"
                safe_msg = msg.encode(encoding, errors="replace").decode(encoding)
                stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class CustomFormatter(logging.Formatter):
    """Clean formatter with ISO timestamp and clear level tags."""

    FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)


def setup_logger(
    name: str = "scraper",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configures and returns a structured logger.

    :param name: Logger name
    :param level: Logging level string (DEBUG, INFO, WARNING, ERROR)
    :param log_file: Optional path to output log file
    :return: Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logger is called repeatedly
    if logger.handlers:
        logger.handlers.clear()

    formatter = CustomFormatter()

    # Safe Console Handler
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional File Handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
