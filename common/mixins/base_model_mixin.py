from .from_pydantic_mixin import PydanticMixin
from .primary_key_mixin import PrimaryKeyMixin
from .timestamp_mixin import TimestampMixin


class BaseModelMixin(PydanticMixin, PrimaryKeyMixin, TimestampMixin):
    """
    Provides essential shared attributes for all database models.

    Includes:
    - UUID-based primary key
    - Creation and update timestamps
    - Pydantic to ORM conversion
    """
