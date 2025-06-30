"""Base Repository for Cricket Fitness Tracker."""

from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, ReadSchemaType, UpdateSchemaType]):
    """Base repository for basic CRUD operations."""

    def __init__(
        self,
        model: type[ModelType],
        session: AsyncSession,
    ) -> None:
        """Initialize the repository."""
        self.model = model
        self.session = session

    async def create(self, record_in: CreateSchemaType) -> ModelType:
        """Create a new database record."""
        try:
            # Convert Pydantic model to dictionary and create SQLAlchemy model
            record_data = record_in.model_dump(exclude_unset=True)
            db_record = self.model(**record_data)

            self.session.add(db_record)
            await self.session.commit()
            await self.session.refresh(db_record)

            return db_record
        except IntegrityError as exc:
            await self.session.rollback()
            msg = "Failed to create record"
            raise ValueError(msg) from exc

    async def read(self, record_id: int) -> ModelType | None:
        """Retrieve a record by its ID."""
        result = await self.session.execute(
            select(self.model).filter(self.model.id == record_id),
        )
        return result.scalar_one_or_none()

    async def read_multi(
        self,
        offset: int = 0,
        limit: int = 100,
        order_by: UnaryExpression | None = None,
    ) -> list[ModelType]:
        """Retrieve multiple records with pagination."""
        query = select(self.model).offset(offset).limit(limit)

        if order_by is not None:
            query = query.order_by(order_by)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(self, record_id: int, update_data: dict) -> ModelType | None:
        """Update an existing record."""
        db_record = await self.read(record_id)
        if db_record is None:
            return None

        for key, value in update_data.items():
            if hasattr(db_record, key):
                setattr(db_record, key, value)

        await self.session.commit()
        await self.session.refresh(db_record)
        return db_record

    async def delete(self, record_id: int) -> ModelType | None:
        """Delete a record by its ID and return the deleted item."""
        db_record = await self.read(record_id)
        if db_record is None:
            return None

        await self.session.delete(db_record)
        await self.session.commit()
        return db_record

    async def count(self) -> int:
        """Get the total count of records in the database."""
        result = await self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()
