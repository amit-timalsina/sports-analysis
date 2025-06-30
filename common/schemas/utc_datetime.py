from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class UTCDateTime(datetime):
    """
    A custom type for Pydantic models that ensures all datetime objects are in UTC.

    This type only accepts timezone-aware datetime objects in UTC.
    It will raise a ValueError for any input that is not a datetime object,
    is not timezone-aware, or is not in UTC.

    Usage:
        class MyModel(BaseModel):
            timestamp: UTCDateTime
    """

    @classmethod
    def now(cls, _=None) -> "UTCDateTime":  # noqa: ANN001
        """
        Get the current UTC time.

        Returns
        -------
            UTCDateTime: The current UTC time.

        """
        return cls(datetime.now(UTC))

    def __new__(cls, *args, **kwargs) -> "UTCDateTime":  # noqa: ANN002, ANN003
        """
        Create a new UTCDateTime instance.

        This method ensures that the datetime is in UTC.

        Returns
        -------
            UTCDateTime: A new instance of UTCDateTime.

        Raises
        ------
            ValueError: If the input is not a valid UTC datetime.

        """
        if len(args) == 0 and len(kwargs) == 0:
            return cls.now()

        if len(args) == 1 and isinstance(args[0], datetime):
            dt = args[0]
        else:
            dt = datetime(*args, **kwargs)  # noqa: DTZ001

        if dt.tzinfo is None:
            msg = "Datetime must be timezone-aware"
            raise ValueError(msg)

        if dt.tzinfo.utcoffset(dt) != timedelta(0):
            msg = "Datetime must have a UTC offset of 0"
            raise ValueError(msg)

        return super().__new__(
            cls,
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo=UTC,
        )

    @classmethod
    def validate_utc_datetime(cls, value: datetime) -> "UTCDateTime":
        """
        Validate that the input is a timezone-aware datetime object in UTC.

        Args:
        ----
            value (Any): The input value to validate.

        Returns:
        -------
            datetime: The validated UTC datetime object.

        Raises:
        ------
            ValueError: If the input is not a datetime object, is not timezone-aware,
            or is not in UTC.

        """
        if isinstance(value, cls):
            return value

        if not isinstance(value, datetime):
            msg = "Input must be a datetime object"
            raise TypeError(msg)

        if value.tzinfo is None:
            msg = "Datetime must be timezone-aware"
            raise ValueError(msg)

        if value.tzinfo.utcoffset(value) != timedelta(0):
            msg = "Datetime must be in UTC timezone"
            raise ValueError(msg)

        return cls(value.replace(tzinfo=UTC))

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,  # noqa: ANN401
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        Define the Pydantic core schema for the UTCDateTime type.

        Args:
        ----
            source_type (Any): The source type (unused in this implementation).
            handler (GetCoreSchemaHandler): The schema handler (unused in this implementation).

        Returns:
        -------
            core_schema.CoreSchema: The core schema for UTCDateTime.

        """
        return core_schema.no_info_after_validator_function(
            cls.validate_utc_datetime,
            core_schema.datetime_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )
