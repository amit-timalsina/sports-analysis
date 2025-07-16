from collections.abc import AsyncGenerator

import svcs
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from auth.exceptions.exceptions import UserCreationError, UserNotFoundError
from auth.models.user import User as UserModel
from auth.schemas.user import UserCreate, UserRead, UserUpdate
from auth.schemas.user_identity import UserIdentityBase
from common.repositories.crud_repository import CRUDRepository
from logger import get_logger

logger = get_logger(__name__)


class UserRepository(CRUDRepository[UserModel, UserCreate, UserRead, UserUpdate]):
    """Repository for managing user-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the user repository.

        Args:
        ----
        session (AsyncSession): The database session to use for operations.

        """
        super().__init__(
            model=UserModel,
            create_schema=UserCreate,
            read_schema=UserRead,
            update_schema=UserUpdate,
            session=session,
            not_found_exception=UserNotFoundError,
            creation_exception=UserCreationError,
        )

    async def read_by_email(self, email: str) -> UserRead:
        """
        Retrieve a user by their email address.

        Args:
        ----
            email (str): The email address of the user to retrieve.

        Returns:
        -------
            UserSchema: The user schema object if found.

        Raises:
        ------
            UserNotFoundError: If no user with the given email is found.

        """
        return await self.read_by_filter(UserModel.email == email)

    async def read_by_identity(self, identity: UserIdentityBase) -> UserRead:
        """
        Retrieve a user by their identity information.

        Args:
        ----
            identity (UserIdentityBase): The identity information of the user to retrieve.

        Returns:
        -------
            UserSchema: The user schema object if found.

        Raises:
        ------
            UserNotFoundError: If no user with the given identity is found.

        """
        """
        TODO: Cache this as follows:
        - For a given identity provider and the provider user id, check the cache
        for the user id and data.
        - If not found, then execute this function.
        - After the query, cache the result.
        - Return the result.

        - Invalidate the cache when:
            - User is updated
            - User is deleted
        """
        stmt = (
            select(UserModel)
            .options(joinedload(UserModel.identities))
            .join(UserModel.identities)
            .where(
                (UserModel.identities.any(provider=identity.provider))
                & (UserModel.identities.any(provider_user_id=identity.provider_user_id)),
            )
        )

        result = await self.session.execute(stmt)

        user = result.unique().scalar_one_or_none()

        if user is None:
            msg = f"User with identity {identity} not found"
            raise UserNotFoundError(msg)

        return self.read_schema.model_validate(user)

    @classmethod
    async def get_as_dependency(
        cls,
        services: svcs.Container,
    ) -> AsyncGenerator["UserRepository", None]:
        """
        Get the user repository as a dependency.

        Args:
        ----
            services (svcs.Container): The service container used for
                dependency injection.

        Yields:
        ------
            UserRepository: The user repository.

        """
        session = await services.aget(AsyncSession)
        yield UserRepository(session)
