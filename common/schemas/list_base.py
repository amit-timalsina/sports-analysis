from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, computed_field

from common.schemas.app_base_model import AppBaseModel

T = TypeVar("T", bound=BaseModel)


class ListBase(AppBaseModel, Generic[T]):
    """
    A generic base class for paginated lists of any Pydantic model.

    This class provides a structure for paginated results, including
    metadata about the pagination and a list of items of the specified type.

    Note: Page numbering starts from 0 and goes up to (total_pages - 1).
    """

    items: list[T] = Field(default_factory=list, description="List of items")
    page: int = Field(..., description="Current page number (0-indexed)", ge=0)
    page_size: int = Field(..., description="Number of items per page", gt=0)
    total_items: int = Field(..., description="Total number of items across all pages", ge=0)

    @property
    @computed_field
    def total_pages(self) -> int:
        """Compute the total number of pages."""
        return ceil(self.total_items / self.page_size)

    @property
    @computed_field
    def has_more(self) -> bool:
        """Determine if there are more pages after the current one."""
        return self.page < (self.total_pages - 1)

    @property
    @computed_field
    def next_page(self) -> int | None:
        """Returns the next page number if there is one, otherwise None."""
        return self.page + 1 if self.has_more else None

    @property
    @computed_field
    def previous_page(self) -> int | None:
        """Returns the previous page number if there is one, otherwise None."""
        return self.page - 1 if self.page > 0 else None
