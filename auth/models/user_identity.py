from typing import ClassVar

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from auth.schemas.identity_provider import IdentityProvider
from common.mixins.relationship_factories import user_relationship_factory
from database.base import ProductionBase


class UserIdentity(
    ProductionBase,
    user_relationship_factory(
        back_populates="identities",
        unique_user_id=False,
        lazy="selectin",
        ondelete="CASCADE",
    ),
):
    """
    Base class for user identities across different providers.

    This class defines common structure for user identities, allowing for
    polymorphic behaviour based on the identity provider.
    """

    __tablename__: ClassVar[str] = "user_identities"

    provider_user_id: Mapped[str] = mapped_column(String, index=True, unique=True)
    provider: Mapped[IdentityProvider] = mapped_column(Enum(IdentityProvider))

    __mapper_args__ = {  # noqa: RUF012
        "polymorphic_on": provider,
    }


class SupabaseIdentity(UserIdentity):
    """Concrete implementation of UserIdentity for Supabase authentication."""

    __mapper_args__: ClassVar[dict[str, IdentityProvider]] = {
        "polymorphic_identity": IdentityProvider.SUPABASE,
    }


class FirebaseIdentity(UserIdentity):
    """Concrete implementation of UserIdentity for Firebase authentication."""

    __mapper_args__: ClassVar[dict[str, IdentityProvider]] = {
        "polymorphic_identity": IdentityProvider.FIREBASE,
    }


identity_class_by_provider: dict[IdentityProvider, type[UserIdentity]] = {
    IdentityProvider.SUPABASE: SupabaseIdentity,
    IdentityProvider.FIREBASE: FirebaseIdentity,
}
