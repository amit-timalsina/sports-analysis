from enum import StrEnum


class KniruLogColor(StrEnum):
    """Color codes for logging."""

    RESET = "\x1b[0m"
    GREEN = "\x1b[38;2;21;172;145m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
