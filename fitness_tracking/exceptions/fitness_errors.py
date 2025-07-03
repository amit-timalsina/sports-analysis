"""Fitness tracking related exceptions."""

from common.exceptions import AppError


class FitnessError(AppError):
    """Base exception for fitness tracking related errors."""

    status_code = 500
    detail = "Fitness tracking operation failed"


class FitnessEntryNotFoundError(FitnessError):
    """Exception raised when a fitness entry is not found."""

    status_code = 404
    detail = "Fitness entry not found"


class FitnessEntryCreationError(FitnessError):
    """Exception raised when fitness entry creation fails."""

    status_code = 400
    detail = "Failed to create fitness entry"


class RestDayEntryNotFoundError(FitnessError):
    """Exception raised when a rest day entry is not found."""

    status_code = 404
    detail = "Rest day entry not found"


class RestDayEntryCreationError(FitnessError):
    """Exception raised when rest day entry creation fails."""

    status_code = 400
    detail = "Failed to create rest day entry"


class CricketCoachingEntryNotFoundError(FitnessError):
    """Exception raised when a cricket coaching entry is not found."""

    status_code = 404
    detail = "Cricket coaching entry not found"


class CricketCoachingEntryCreationError(FitnessError):
    """Exception raised when cricket coaching entry creation fails."""

    status_code = 400
    detail = "Failed to create cricket coaching entry"


class CricketMatchEntryNotFoundError(FitnessError):
    """Exception raised when a cricket match entry is not found."""

    status_code = 404
    detail = "Cricket match entry not found"


class CricketMatchEntryCreationError(FitnessError):
    """Exception raised when cricket match entry creation fails."""

    status_code = 400
    detail = "Failed to create cricket match entry"


class InvalidActivityDataError(FitnessError):
    """Exception raised when activity data is invalid."""

    status_code = 400
    detail = "Invalid activity data provided"


class ConversationNotLinkedError(FitnessError):
    """Exception raised when activity entry is not properly linked to conversation."""

    status_code = 400
    detail = "Activity entry must be linked to a conversation"
