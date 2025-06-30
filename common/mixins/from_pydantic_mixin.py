from typing import Self, TypeVar

from pydantic import BaseModel
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.mapper import Mapper

T = TypeVar("T", bound="PydanticMixin")


class PydanticMixin:
    """Mixin for adding capabilities to a SQLAlchemy model to be created from a Pydantic model."""

    @classmethod
    def _handle_polymorphic_model(cls, mapper: Mapper, data: dict) -> tuple:
        """Handle polymorphic model logic and return updated mapper."""
        polymorphic_on = mapper.polymorphic_on
        if polymorphic_on is None:
            return mapper, cls

        discrim_col_name = polymorphic_on.key
        discrim_value = data.get(discrim_col_name)
        if discrim_value is None:
            msg = f"Discriminator field '{discrim_col_name}' is required for '{cls.__name__}'"
            raise ValueError(msg)

        target_class = next(
            (
                subclass_mapper.class_
                for subclass_mapper in mapper.self_and_descendants
                if subclass_mapper.polymorphic_identity == discrim_value
            ),
            None,
        )
        if target_class is None:
            msg = f"Unknown polymorphic identity '{discrim_value}' for '{cls.__name__}'"
            raise ValueError(msg)

        return inspect(target_class), target_class

    @classmethod
    def _handle_relationships(
        cls,
        orm_model: T,
        mapper: Mapper,
        data: dict,
        session: AsyncSession,
    ) -> None:
        """Handle model relationships."""
        if mapper.relationships is None:
            return

        for relationship in mapper.relationships:
            if relationship.key not in data:
                continue

            related_data = data[relationship.key]
            if isinstance(related_data, list):
                related_models = [
                    relationship.mapper.class_.from_pydantic(item, session) for item in related_data
                ]
                setattr(orm_model, relationship.key, related_models)
            elif isinstance(related_data, dict):
                related_model = relationship.mapper.class_.from_pydantic(
                    related_data,
                    session,
                )
                setattr(orm_model, relationship.key, related_model)

    @classmethod
    def from_pydantic(cls, pydantic_model: BaseModel, session: AsyncSession) -> Self:
        """Convert a Pydantic model instance to a SQLAlchemy ORM model instance."""
        data = (
            pydantic_model.model_dump() if isinstance(pydantic_model, BaseModel) else pydantic_model
        )

        mapper = inspect(cls)
        if mapper is None:
            return cls()

        mapper, target_class = cls._handle_polymorphic_model(mapper, data)
        orm_model: Self = target_class()

        for column in mapper.columns:
            if column.key in data:
                setattr(orm_model, column.key, data[column.key])

        cls._handle_relationships(orm_model, mapper, data, session)
        return orm_model
