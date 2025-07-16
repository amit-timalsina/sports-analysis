import logging

from .config import get_log_settings
from .log_formatter import KniruLogFormatter

log_settings = get_log_settings()


def get_logger(
    logger_name: str,
    log_level: int | str = log_settings.level,
) -> logging.Logger:
    """Use this function to get a logger in different modules."""
    # Create a logger with the specified name.
    # Tip: Use __name__ as the logger name in each module.
    logger = logging.getLogger(logger_name)

    # Configure logging level
    logger.setLevel(log_level)

    # Create a stream handler to log message to console.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(KniruLogFormatter())
    stream_handler.setLevel(log_level)

    # Add the handler to the logger only if it doesn't already exist.
    if not logger.handlers:
        logger.addHandler(stream_handler)

    logger.propagate = False

    return logger
