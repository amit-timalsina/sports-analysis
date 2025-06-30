from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression


class UtcNow(expression.FunctionElement):
    """
    Custom SQLAlchemy expression for generating the UTC timestamps.

    This class extends FunctionElement to create a custom SQL function
    that returns the current UTC timestamp.

    Attributes:
        type (DateTime): The SQL type for the timestamp, set to DateTime with timezone.
        inherit_cache (bool): Indicates whether to inherit the caching behavior from the
            parent class.

    """

    type = DateTime(timezone=True)
    inherit_cache = True


@compiles(UtcNow, "postgresql")
def pg_utcnow(element: Any, compiler: Any, **kw: Any) -> str:  # noqa: ANN401, ARG001
    """
    Compiles the UtcNow expression for PostgreSQL.

    Args:
        element (Any): The UtcNow instance to be compiled.
        compiler (Any): The SQL Compiler.
        **kw (Any): Additional keyword arguments.

    Returns:
        str: The PostgreSQL-specific SQL expression for current UTC timestamp.

    """
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


@compiles(UtcNow, "sqlite")
def sqlite_utcnow(element: Any, compiler: Any, **kw: Any) -> str:  # noqa: ANN401, ARG001
    """
    Compiles the UtcNow expression for SQLite.

    Args:
        element (Any): The UtcNow instance to be compiled.
        compiler (Any): The SQL Compiler.
        **kw (Any): Additional keyword arguments.

    Returns:
        str: The SQLite-specific SQL expression for current UTC timestamp.

    """
    return "CURRENT_TIMESTAMP"


class UTCDateTime(TypeDecorator):
    """
    Ensures that datetime objects are always UTC-aware.

    This class extends TypeDecorator to convert naive datetime
    objects to UTC-aware datetime objects.

    Attributes:
        impl (DateTime): The underlying DateTime type with timezone support.
        cache_ok (bool): Indicates whether this type is save to cache.

    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Any) -> datetime | None:  # noqa: ANN401, ARG002
        """
        Convert the datetime object to UTC before binding it to the parameter.

        Args:
            value: The datetime value to be processed.
            dialect: The database dialect.

        Returns:
            datetime | None: The processed datetime value with UTC timezone.

        """
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value

    def process_result_value(self, value: datetime | None, dialect: Any) -> datetime | None:  # noqa: ANN401, ARG002
        """
        Convert the datetime object to UTC after retrieving it from the result.

        Args:
            value (DateTime | None): The datetime object to be processed.
            dialect (Any): The SQL dialect.

        Returns:
            datetime | None: The processed datetime object.

        """
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class TimestampMixin:
    """
    Mixin for adding creation and update timestamps to a model.

    This mixin adds 'created_at' and 'updated_at' columns to a model,
    automatically setting and updating these timestamps.

    Attributes
    ----------
        created_at (Mapped[datetime]): The timestamp when the record was created.
        updated_at (Mapped[datetime]): The timestamp when the record was last updated.

    """

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        server_default=UtcNow(),
        comment="Record creation timestamp.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        server_default=UtcNow(),
        onupdate=UtcNow(),
        comment="Record last update timestamp.",
    )
