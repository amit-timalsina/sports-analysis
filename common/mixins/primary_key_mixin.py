import uuid

from sqlalchemy import UUID
from sqlalchemy.orm import Mapped, mapped_column


class PrimaryKeyMixin:
    """Mixin that adds a UUID-based primary key for all tables."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        unique=True,
        default=uuid.uuid4,
        comment="Unique identifier for the record (Primary Key).",
    )
