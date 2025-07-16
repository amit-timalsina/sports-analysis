from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth.models.user_identity import UserIdentity
from database.base import ProductionBase


class User(ProductionBase):
    """Represents a user in the database."""

    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(
        String(32),
        nullable=True,
        comment="User's first name",
    )

    last_name: Mapped[str] = mapped_column(
        String(32),
        nullable=True,
        comment="User's last name",
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        index=True,
        comment="User's phone number",
    )

    email: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        unique=True,
        index=True,
        comment="User's email address",
    )

    # The 'identities' relationship represents the various authentication methods
    # or identity providers associated with a user. This allows for a flexible
    # authentication system where a single user can have multiple ways to log in.
    #
    # Benefits of multiple identities:
    # 1. Flexibility: Users can choose their preferred login method.
    # 2. Security: Provides backup login options if one method is compromised.
    # 3. Integration: Easily connect with different third-party authentication providers.
    # 4. User Experience: Allows for seamless social logins and account linking.
    identities: Mapped[list[UserIdentity]] = relationship(
        "UserIdentity",
        cascade="all, delete-orphan",
        back_populates="user",
        uselist=True,
        lazy="selectin",
    )
