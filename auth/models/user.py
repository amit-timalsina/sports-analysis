from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth.models.user_identity import UserIdentity
from database.base import ProductionBase
from fitness_tracking.models.cricket_coaching import CricketCoachingEntry
from fitness_tracking.models.cricket_match import CricketMatchEntry
from fitness_tracking.models.fitness import FitnessEntry
from fitness_tracking.models.rest_day import RestDayEntry
from voice_processing.models.conversation import Conversation


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
    conversations: Mapped[list[Conversation]] = relationship(
        cascade="all, delete-orphan",
        back_populates="user",
        order_by="Conversation.created_at",
    )
    cricket_match_entries: Mapped[list[CricketMatchEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cricket_coaching_entries: Mapped[list[CricketCoachingEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    fitness_entries: Mapped[list[FitnessEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    rest_day_entries: Mapped[list[RestDayEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
