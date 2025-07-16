"""
Provides a centralized logger for the application.

Usage:
    from logger import get_logger
    logger = get_logger(__name__)

    logger.info("<Add your message here>")
    logger.debug("<Add your message here>")
    logger.warning("<Add your message here>")
    logger.error("<Add your message here>")
    logger.critical("<Add your message here>")
"""

import logging

from .log_filters import RootEndpointFilter
from .logger import get_logger

__all__ = (
    "RootEndpointFilter",
    "get_logger",
)
logging.getLogger("uvicorn.access").addFilter(RootEndpointFilter())
