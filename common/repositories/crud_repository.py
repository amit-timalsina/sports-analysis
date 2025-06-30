"""
Generic CRUD repository Module.

This module provides a generic CRUD (Create, Read, Update, Delete) repository for
SQLAlchemy models. It aims to reduce boilerplate code and provide a consistent
interface for database operations across differnent models.

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
from collections.abc import AsyncGenerator, Callable
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, TypeAdapter
from sqlalchemy import BinaryExpression, ColumnElement, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import UnaryExpression

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=CommonBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
ReadSchemaType = TypeVar("ReadSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDRepository(Generic[ModelType, CreateSchemaType, ReadSchemaType, UpdateSchemaType]):
    """
    Generic CRUD repository for database operations.

    This class provides basic CRUD operations for a given SQLAlchemy model.
    It uses Pydantic models for data validation and serialization.

    Attributes
    ----------
        model: Type[ModelType]: The SQLAlchemy model to perform operations on.
        create_schema: Type[CreateSchemaType]: Pydantic model for record creation.
        read_schema: Type[ReadSchemaType]: Pydantic model for record reading.
        update_schema: Type[UpdateSchemaType]: Pydantic model for record updating.
        session: Union[AsyncSession, AsyncGenerator[AsyncSession, None]]:
            The SQLAlchemy session or session generator.
        not_found_exception: Type[Exception]: Exception to raise when a record is not found.
        creation_exception: Type[Exception]: Exception to raise when record creation fails.
        user_filter: Callable[[Optional[User]], BinaryExpression]:
            A callable that returns a SQLAlchemy filter expression for user filtering.
        project_filter: Callable[[Optional[UUID]], BinaryExpression]:
            A callable that returns a SQLAlchemy filter expression for project filtering.

    """

    def __init__(  # noqa: PLR0913
        self,
        model: type[ModelType],
        create_schema: type[CreateSchemaType],
        read_schema: type[ReadSchemaType],
        update_schema: type[UpdateSchemaType],
        session: AsyncSession | AsyncGenerator[AsyncSession, None],
        not_found_exception: type[Exception],
        creation_exception: type[Exception],
        user_filter: Callable[[User | None], BinaryExpression] = lambda x: (x is None)  # type: ignore[assignment]
        or (x.id == UserModel.id),  # type: ignore[return-value]
        project_filter: Callable[[UUID | None], BinaryExpression] = lambda x: (x is None)  # type: ignore[assignment]
        or (x == ProjectModel.id),  # type: ignore[return-value]
    ) -> None:
        """
        Initialize the CRUDRepository.

        Args:
        ----
        model : type[ModelType]
            The SQLAlchemy model class.
        create_schema : type[CreateSchemaType]
            The Pydantic model class for record creation.
        read_schema : type[ReadSchemaType]
            The Pydantic model class for reading records.
        update_schema : type[UpdateSchemaType]
            The Pydantic model class for updating records.
        session : Union[AsyncSession, AsyncGenerator[AsyncSession, None]]
            The database session or a generator that yields database sessions.
        not_found_exception : type[Exception]
            Exception to raise when a record is not found.
        creation_exception : type[Exception]
            Exception to raise when record creation fails.
        user_filter : Callable[[Optional[User]], BinaryExpression], optional
            Function to generate user-specific filter condition (default is lambda _: True).
        project_filter : Callable[[UUID | None], BinaryExpression], optional
            Function to generate project-specific filter condition (default is lambda _: True).

        Raises:
        ------
        TypeError
            If the session is neither AsyncSession nor AsyncGenerator

        """
        if not isinstance(session, AsyncSession):
            error_msg = "AsyncGenerator is not supported yet. Please use AsyncSession."
            raise TypeError(error_msg)

        self.model = model
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.update_schema = update_schema
        self.session = session
        self.not_found_exception = not_found_exception
        self.creation_exception = creation_exception
        self.user_filter = user_filter
        self.project_filter = project_filter

    async def get_session(self) -> AsyncSession:
        """
        Get the current session or yield a new one from the generator.

        Returns
        -------
        AsyncSession
            The current database session

        Raises
        ------
        TypeError
            If the session is neither AsyncSession nor AsyncGenerator

        """
        match self.session:
            case AsyncSession():
                return self.session
            case AsyncGenerator():
                # TODO (Amit): Make sure to close the session too.
                # This will be important when the generator is passed since session
                # will be created internally so it is our responsibility to close it.
                return await anext(self.session)
            case _:
                error_msg = (
                    "Session must be either AsyncSession or AsyncGenerator "
                    "which yields AsyncSession"
                )
                raise TypeError(error_msg)

    async def create(
        self,
        record_in: CreateSchemaType,
        current_user: User | None = None,
    ) -> ReadSchemaType:
        """
        Create a new database record.

        Args:
        ----
        record_in : CreateSchemaType
            The data for creating a new record.
        current_user : User | None, optional
            The current user (default is None) for access restriction..

        Returns:
        -------
        ReadSchemaType
            The created record.

        Raises:
        ------
        CreationException
            If the record creation fails.

        """
        session = await self.get_session()
        try:
            db_record = self.model.from_pydantic(record_in, session)
            if current_user:
                db_record.user_id = current_user.id  # type: ignore[attr-defined]
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
        current_user: User | None = None,
        project_id: UUID | None = None,
    ) -> ReadSchemaType:
        """
        Retrieve a record by its ID.

        Args:
        ----
        record_id : UUID
            The ID of the record to retrieve
        project_id : Optional[UUID], optional
            The project ID for access restriction (default is None)
        current_user : Optional[User], optional
            The current user for access restriction (default is None)
        project_id : Optional[UUID], optional
            The project ID for access restriction (default is None)

        Returns:
        -------
        ReadSchemaType
            The retrieved record

        Raises:
        ------
        not_found_exception
            If the record with the given ID is not found

        """
        return await self.read_by_filter(self.model.id == record_id, current_user, project_id)  # type: ignore[arg-type]

    async def read_by_filter(
        self,
        filter_condition: BinaryExpression,
        current_user: User | None = None,
        project_id: UUID | None = None,
    ) -> ReadSchemaType:
        """
        Retrieve a record based on a filter condition.

        Args:
        ----
        filter_condition : BinaryExpression
            The SQLAlchemy filter condition to apply
        current_user : Optional[User], optional
            The current user for access restriction (default is None)
        project_id : Optional[UUID], optional
            The project ID for access restriction (default is None)

        Returns:
        -------
        ReadSchemaType
            The retrieved record

        Raises:
        ------
        not_found_exception
            If no record is found matching the filter condition

        """
        session = await self.get_session()
        result = await session.execute(
            select(self.model)
            .filter(filter_condition)
            .filter(self.user_filter(current_user))
            .filter(self.project_filter(project_id)),
        )
        db_record = result.scalar_one_or_none()
        if db_record is None:
            msg = "Record not found"
            raise self.not_found_exception(msg)
        return self._to_read_schema(db_record)

    async def read_multi(
        self,
        current_user: User | None = None,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: UnaryExpression | None = None,
    ) -> list[ReadSchemaType]:
        """
        Retrieve multiple records with pagination.

        Args:
        ----
        current_user : Optional[User], optional
            The current user for access restriction (default is None)
        project_id : Optional[UUID], optional
            Filter records by project ID (default is None)
        offset : int, optional
            Number of records to offset (default is 0)
        limit : int, optional
            Maximum number of records to return (default is 100)
        order_by : UnaryExpression | None, optional
            SQLAlchemy order by clause (default is None)

        Returns:
        -------
        list[ReadSchemaType]
            List of retrieved records

        """
        session = await self.get_session()
        query = (
            select(self.model)
            .filter(self.user_filter(current_user))
            .filter(self.project_filter(project_id))
            .offset(offset)
            .limit(limit)
        )
        if order_by is not None:
            query = query.order_by(order_by)
        result = await session.execute(query)
        return [self._to_read_schema(record) for record in result.scalars().all()]

    async def read_multi_by_filter(
        self,
        filter_condition: ColumnElement[bool],
        current_user: User | None = None,
        project_id: UUID | None = None,
        offset: int = 0,
        limit: int = 100,
        order_by: UnaryExpression | None = None,
    ) -> list[ReadSchemaType]:
        """
        Retrieve multiple records based on a filter condition with pagination.

        Args:
        ----
        filter_condition : BinaryExpression
            The SQLAlchemy filter condition to apply
        current_user : Optional[User], optional
            The current user for access restriction (default is None)
        project_id : Optional[UUID], optional
            Filter records by project ID (default is None)
        offset : int, optional
            Number of records to offset (default is 0)
        limit : int, optional
            Maximum number of records to return (default is 100)
        order_by : UnaryExpression | None, optional
            SQLAlchemy order by clause (default is None)

        Returns:
        -------
        list[ReadSchemaType]
            List of retrieved records

        """
        session = await self.get_session()
        query = (
            select(self.model)
            .filter(filter_condition)
            .filter(self.user_filter(current_user))
            .filter(self.project_filter(project_id))
            .offset(offset)
            .limit(limit)
        )
        if order_by is not None:
            query = query.order_by(order_by)
        result = await session.execute(query)
        return [self._to_read_schema(record) for record in result.scalars().all()]

    async def update(
        self,
        record_id: UUID,
        update_record_in: UpdateSchemaType,
        current_user: User | None = None,
    ) -> ReadSchemaType:
        """
        Update an existing record.

        Args:
        ----
        record_id : UUID
            The ID of the record to update
        update_record_in : UpdateSchemaType
            The updated data for the record
        current_user : Optional[User], optional
            The current user for access restriction (default is None)

        Returns:
        -------
        ReadSchemaType
            The updated record

        Raises:
        ------
        not_found_exception
            If the record with the given ID is not found

        """
        session = await self.get_session()
        db_record = await self._get_db_record(record_id, current_user)
        update_data = update_record_in.model_dump(exclude_unset=True)

        self._update_model_from_dict(db_record, update_data)

        await session.commit()
        await session.refresh(db_record)
        return self._to_read_schema(db_record)

    def _update_model_from_dict(self, db_model: ModelType, update_data: dict) -> None:
        """
        Update a database model from a dictionary.

        Args:
        ----
        db_model : ModelType
            The database model to update
        update_data : dict
            The dictionary containing the updated data

        """
        for key, value in update_data.items():
            if hasattr(db_model, key):
                attr = getattr(db_model, key)
                if isinstance(value, dict) and hasattr(attr, "__dict__"):
                    # Recursively update nested ORM model
                    self._update_model_from_dict(attr, value)
                else:
                    setattr(db_model, key, value)

    async def delete(self, record_id: UUID, current_user: User | None = None) -> ReadSchemaType:
        """
        Delete a record by its ID and return the deleted item.

        Args:
        ----
        record_id : UUID
            The ID of the record to delete
        current_user : Optional[User], optional
            The current user for access restriction (default is None)

        Returns:
        -------
        ReadSchemaType
            The deleted record

        Raises:
        ------
        not_found_exception
            If the record with the given ID is not found

        """
        session = await self.get_session()
        db_record = await self._get_db_record(record_id, current_user)
        result = self._to_read_schema(db_record)
        await session.delete(db_record)
        await session.commit()
        return result

    async def exists(self, record_id: UUID, current_user: User | None = None) -> bool:
        """
        Check if a record with the given ID exists.

        Args:
        ----
        record_id : UUID
            The ID of the record to check
        current_user : Optional[User], optional
            The current user for access restriction (default is None)

        Returns:
        -------
        bool
            True if the record exists, False otherwise

        """
        session = await self.get_session()
        result = await session.execute(
            select(self.model).filter(
                (self.model.id == record_id) & self.user_filter(current_user),
            ),
        )
        return result.scalar_one_or_none() is not None

    async def count(self, current_user: User | None = None, project_id: UUID | None = None) -> int:
        """
        Get the total count of records in the database.

        Args:
        ----
        current_user : Optional[User], optional
            The current user for access restriction (default is None)
        project_id : Optional[UUID], optional
            Filter records by project ID (default is None)

        Returns:
        -------
        int
            The total number of records

        """
        session = await self.get_session()
        result = await session.execute(
            select(func.count(self.model.id))
            .filter(self.user_filter(current_user))
            .filter(self.project_filter(project_id)),
        )
        return result.scalar_one()

    async def count_filtered(
        self,
        filter_condition: ColumnElement[bool],
        current_user: User | None = None,
        project_id: UUID | None = None,
    ) -> int:
        """
        Get the total count of records matching a filter condition.

        Args:
        ----
        filter_condition : ColumnElement[bool]
            The SQLAlchemy filter condition to apply
        current_user : Optional[User], optional
            The current user for access restriction (default is None)
        project_id : Optional[UUID], optional
            Filter records by project ID (default is None)

        Returns:
        -------
        int
            The total number of records matching the filter

        """
        session = await self.get_session()
        result = await session.execute(
            select(func.count(self.model.id))
            .filter(filter_condition)
            .filter(self.user_filter(current_user))
            .filter(self.project_filter(project_id)),
        )
        return result.scalar_one()

    def _to_read_schema(self, db_record: ModelType) -> ReadSchemaType:
        """
        Convert a database record to a Pydantic read schema.

        Args:
        ----
        db_record : ModelType
            The database record to convert

        Returns:
        -------
        ReadSchemaType
            The Pydantic schema representation of the record

        """
        # The TypeAdapter class in Pydantic v2 is designed to handle any type annotations,
        # including single models, unions, and annotated types.
        adapter = TypeAdapter(self.read_schema)
        return adapter.validate_python(db_record)

    async def _get_db_record(
        self,
        record_id: UUID,
        current_user: User | None = None,
    ) -> ModelType:
        """
        Retrieve a database record by its ID.

        Args:
        ----
        record_id : UUID
            The ID of the record to retrieve
        current_user : Optional[User], optional
            The current user for access restriction (default is None)

        Returns:
        -------
        ModelType
            The database record

        Raises:
        ------
        not_found_exception
            If the record with the given ID is not found

        """
        session = await self.get_session()
        result = await session.execute(
            select(self.model).filter(
                (self.model.id == record_id) & self.user_filter(current_user),
            ),
        )
        db_record = result.scalar_one_or_none()
        if db_record is None:
            msg = "Record not found"
            raise self.not_found_exception(msg)
        return db_record
