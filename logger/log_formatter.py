import logging
from typing import ClassVar

from .log_color import KniruLogColor


class KniruLogFormatter(logging.Formatter):
    """Formatter for logging."""

    base_format = (
        "%(levelname)s (%(name)s)" + KniruLogColor.RESET + " [%(pathname)s:%(lineno)d]: %(message)s"
    )

    FORMATS: ClassVar[dict[int, str]] = {
        logging.DEBUG: KniruLogColor.GREEN + base_format,
        logging.INFO: KniruLogColor.GREEN + base_format,
        logging.WARNING: KniruLogColor.YELLOW + base_format,
        logging.ERROR: KniruLogColor.RED + base_format,
        logging.CRITICAL: KniruLogColor.BOLD_RED + base_format,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record by applying the color and KniruLogFormatter."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
