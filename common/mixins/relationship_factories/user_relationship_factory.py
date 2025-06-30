import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.relationships import _LazyLoadArgumentType

if TYPE_CHECKING:
    from auth.models.user import User


def user_relationship_factory(
    back_populates: str,
    *,
    unique_user_id: bool = False,
    lazy: _LazyLoadArgumentType = "select",
    ondelete: str = "CASCADE",
    nullable: bool = False,
) -> type:
    """
    Create a UserRelationshipMixin with the specified parameters.

    This function generates a mixin class that can be used to add a user relationship to SQLAlchemy
    models.


    Args:
        back_populates: The name of the attribute on the User model that this relationship
            should populate.
        unique_user_id: If True, the user_id column will have a unique constraint.
            Defaults to False.
        lazy: The loading strategy for the relationship. Defaults to "select".
        ondelete: The ondelete behaviour for the foreign key. Defaults to "CASCADE".
        nullable: If True, the user_id column will be nullable. Defaults to False.

    Returns:
        Type[UserRelationshipMixin]: A UserRelationshipMixin class that can be used as a mixin
            for SQLAlchemy models.
    Usage:
    ```python
    from common.mixins.relationship_factories.user_relationship_factory import (
        user_relationship_factory
    )

    class Post(Base, user_relationship_factory(back_populates="post")):
        __tablename__ = "posts"
        title: Mapped[str]
        content: Mapped[str]
    ```

    This will add a `user_id` column and a `user` relationship to the `Post` model,
    with a back-reference to the `User` model named `posts`. The caller will need to manually
    define the relationship on the `User` model.

    """

    class UserRelationshipMixin:
        """Mixins for models that have a user relationship."""

        user_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey(
                "users.id",
                ondelete=ondelete,
            ),
            index=True,
            unique=unique_user_id,
            nullable=nullable,
        )

        @declared_attr
        def user(cls) -> Mapped["User"]:  # noqa: N805
            """
            Relationship to the user model.

            This property creates a relationship between the current model and the User model.
            It uses the parameters specified in the factory function to configure the relationship.

            Returns:
                Mapped[User]: A SQLAlchemy relationship to the User model.

            """
            return relationship(
                "User",
                back_populates=back_populates,
                uselist=False,
                lazy=lazy,
            )

    return UserRelationshipMixin
