import logging


class RootEndpointFilter(logging.Filter):
    """
    Custom filter to exclude root endpoint access logs.

    Removes GET / HTTP/1.1 requests from logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out root endpoint access logs."""
        return "GET / " not in record.getMessage()
