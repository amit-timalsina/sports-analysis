from typing import Annotated, Self

import phonenumbers
from phonenumbers import PhoneNumber
from pydantic import EmailStr, Field, model_validator
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

from auth.schemas.user_identity import UserIdentityBase
from common.schemas import PrimaryKeyBase, TimestampBase
from common.schemas.app_base_model import AppBaseModel

# International standard for phone number formatting.
# It's the most compact and globally unique way to represent a phone number.
PHONE_NUMBER_FORMAT = "E164"  # TODO (Amit): This should be configurable.

# TODO (Amit): "US" should be configurable.
AppPhoneNumber = Annotated[
    str | PhoneNumber,
    PhoneNumberValidator(default_region="US", number_format=PHONE_NUMBER_FORMAT),
]


class UserBase(AppBaseModel):
    """Represents a user."""

    first_name: str | None = Field(default=None, max_length=32, description="User's first name.")
    last_name: str | None = Field(default=None, max_length=32, description="User's last name.")
    phone_number: str | None = Field(default=None, description="User's phone number.")
    email: EmailStr | None = Field(default=None, description="User's email address.")

    def to_phone_number(self) -> PhoneNumber | None:
        """Conver the phone_number to PhoneNumber object."""
        if self.phone_number is None:
            return None

        return phonenumbers.parse(self.phone_number)


class UserCreate(UserBase):
    """Schema for creating a user."""

    email: EmailStr | None = Field(default=None, description="User's email address.")
    identities: list[UserIdentityBase] = Field(
        ...,
        min_length=1,
        description="List of user identities.",
    )

    @model_validator(mode="after")
    def validate_identities(self) -> Self:
        """Ensure atleast one identity provider is provided."""
        if not self.identities:
            msg = "Atleast one identity provider is required."
            raise ValueError(msg)

        return self


class User(UserCreate, PrimaryKeyBase, TimestampBase):
    """Represents a user."""


class UserRead(User):
    """Schema for reading a user."""


class UserUpdate(UserBase):
    """Schema for updating a user."""
