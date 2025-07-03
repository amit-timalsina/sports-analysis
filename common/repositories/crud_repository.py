"""
Generic CRUD repository Module.

This module provides a generic CRUD repository for SQLAlchemy models.
It aims to reduce boilerplate code and provide a consistent interface
for database operations across different models.

Usage:
1. Create a specific repository class that inherits from CRUDRepository
2. Provide the SQLAlchemy model, Pydantic Models, and custom exceptions
3. Optionally overrride the methods to add custom behavior

Example:
-------
class UserRepository(
    CRUDRepository[
        User,
        UserCreate,
        UserRead,
        UserUpdate,
    ],
):
    def __init__(self, session: AsyncSession):
        super().__init__(
            model=User,
            create_schema=UserCreate,
            read_schema=UserRead,
            update_schema=UserUpdate,
            session=session,
            not_found_exception=UserNotFound,
            creation_exception=UserCreationError,
        )

    async def read_by_first_name(
        self,
        first_name: int,
    ):
        return await self.read_by_filter(
            self.model.first_name == first_name,
        )

Note:
----
While this generic repository provides a good starting point, it's designed
to be flexible. Feel free to override methods in your specific repositories
to add custom logic or additional error handling as needed.

"""

import logging
from collections.abc import Callable
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import BinaryExpression, ColumnElement, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDRepository(Generic[ModelType, CreateSchemaType, ReadSchemaType, UpdateSchemaType]):
    """
    Generic CRUD repository for database operations.

    This class provides basic CRUD operations for a given SQLAlchemy model.
    It uses Pydantic models for data validation and serialization.
    """

    def __init__(
        self,
        model: type[ModelType],
        create_schema: type[CreateSchemaType],
        read_schema: type[ReadSchemaType],
        update_schema: type[UpdateSchemaType],
        session: AsyncSession,
        not_found_exception: type[Exception],
        creation_exception: type[Exception],
        user_filter: Callable[[Any], Any] | None = None,
        project_filter: Callable[[Any], Any] | None = None,
    ) -> None:
        """Initialize the CRUDRepository."""
        self.model = model
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema
        self.session = session
        self.not_found_exception = not_found_exception
        self.creation_exception = creation_exception
        self.user_filter = user_filter or (lambda x: True)
        self.project_filter = project_filter or (lambda x: True)

    async def get_session(self) -> AsyncSession:
        """Get the current session."""
        return self.session

    async def create(
        self,
        record_in: CreateSchemaType,
        current_user: Any = None,
    ) -> ReadSchemaType:
        """Create a new database record."""
        session = await self.get_session()
        try:
            # Convert Pydantic model to dict and create SQLAlchemy model
            record_data = record_in.model_dump()
            db_record = self.model(**record_data)
            session.add(db_record)
            await session.commit()
            await session.refresh(db_record)
            return self._to_read_schema(db_record)
        except IntegrityError as exc:
            await session.rollback()
            msg = "Failed to create record"
            raise self.creation_exception(msg) from exc

    async def read(
        self,
        record_id: UUID,
        current_user: Any = None,
        project_id: UUID | None = None,
    ) -> ReadSchemaType:
        """Retrieve a record by its ID."""
        return await self.read_by_filter(
            self.model.id == record_id,
            current_user,
            project_id,
        )

    async def read_by_filter(
        self,
        filter_condition: BinaryExpression,
        current_user: Any = None,
        project_id: UUID | None = None,
    ) -> ReadSchemaType:
        """Retrieve a record based on a filter condition."""
        session = await self.get_session()
        result = await session.execute(
            select(self.model).filter(filter_condition),
        )
        db_record = result.scalar_one_or_none()
        if db_record is None:
            msg = "Record not found"
            raise self.not_found_exception(msg)
        return self._to_read_schema(db_record)

    async def read_multi(
        self,
        current_user: Any = None,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: UnaryExpression | None = None,
    ) -> list[ReadSchemaType]:
        """Retrieve multiple records with pagination."""
        session = await self.get_session()
        query = select(self.model).offset(offset).limit(limit)

        if order_by is not None:
            query = query.order_by(order_by)

        result = await session.execute(query)
        return [self._to_read_schema(record) for record in result.scalars().all()]

    async def read_multi_by_filter(
        self,
        filter_condition: ColumnElement[bool],
        current_user: Any = None,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: UnaryExpression | None = None,
    ) -> list[ReadSchemaType]:
        """Retrieve multiple records based on a filter condition with pagination."""
        session = await self.get_session()
        query = select(self.model).filter(filter_condition).offset(offset).limit(limit)

        if order_by is not None:
            query = query.order_by(order_by)

        result = await session.execute(query)
        return [self._to_read_schema(record) for record in result.scalars().all()]

    async def update(
        self,
        record_id: UUID,
        update_record_in: UpdateSchemaType,
        current_user: Any = None,
    ) -> ReadSchemaType:
        """Update an existing record."""
        session = await self.get_session()
        db_record = await self._get_db_record(record_id, current_user)
        update_data = update_record_in.model_dump(exclude_unset=True)

        self._update_model_from_dict(db_record, update_data)

        await session.commit()
        await session.refresh(db_record)
        return self._to_read_schema(db_record)

    def _update_model_from_dict(self, db_model: ModelType, update_data: dict) -> None:
        """Update a database model from a dictionary."""
        for key, value in update_data.items():
            if hasattr(db_model, key):
                setattr(db_model, key, value)

    async def delete(self, record_id: UUID, current_user: Any = None) -> ReadSchemaType:
        """Delete a record by its ID and return the deleted item."""
        session = await self.get_session()
        db_record = await self._get_db_record(record_id, current_user)
        result = self._to_read_schema(db_record)
        await session.delete(db_record)
        await session.commit()
        return result

    async def exists(self, record_id: UUID, current_user: Any = None) -> bool:
        """Check if a record with the given ID exists."""
        session = await self.get_session()
        result = await session.execute(
            select(self.model).filter(self.model.id == record_id),
        )
        return result.scalar_one_or_none() is not None

    async def count(self, current_user: Any = None, project_id: UUID | None = None) -> int:
        """Count the total number of records."""
        session = await self.get_session()
        result = await session.execute(select(func.count(self.model.id)))
        return result.scalar() or 0

    async def count_filtered(
        self,
        filter_condition: ColumnElement[bool],
        current_user: Any = None,
        project_id: UUID | None = None,
    ) -> int:
        """Count records that match the filter condition."""
        session = await self.get_session()
        result = await session.execute(
            select(func.count(self.model.id)).filter(filter_condition),
        )
        return result.scalar() or 0

    def _to_read_schema(self, db_record: ModelType) -> ReadSchemaType:
        """Convert a database record to the read schema."""
        # Convert SQLAlchemy model to dict, then to Pydantic model
        record_dict = {}
        for column in db_record.__table__.columns:
            record_dict[column.name] = getattr(db_record, column.name)
        return self.read_schema(**record_dict)

    async def _get_db_record(
        self,
        record_id: UUID,
        current_user: Any = None,
    ) -> ModelType:
        """Get a database record by ID with user filtering."""
        session = await self.get_session()
        result = await session.execute(
            select(self.model).filter(self.model.id == record_id),
        )
        db_record = result.scalar_one_or_none()
        if db_record is None:
            msg = "Record not found"
            raise self.not_found_exception(msg)
        return db_record
