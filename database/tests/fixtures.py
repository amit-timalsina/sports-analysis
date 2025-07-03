from collections.abc import AsyncGenerator, Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Database URL for testing (use an in-memory SQLite database)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def engine() -> AsyncEngine:
    """
    Create and return an AsyncEngine instance for testing.

    Returns
    -------
    AsyncEngine
        An instance of AsyncEngine configured for testing.

    """
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="module")
def async_session_maker(engine: AsyncEngine) -> Callable[..., AsyncSession]:
    """
    Create and return a session maker for AsyncSession.

    Args:
    ----
    engine : AsyncEngine
        The AsyncEngine instance to use for creating sessions.

    Returns:
    -------
    Callable[..., AsyncSession]
        A session maker function that creates AsyncSession instances.

    """
    return sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# IMPORTANT: Make sure to not change scope
# DO NOT USE scope="module" for db_session fixture.
# All tests should run on a fresh session.
@pytest.fixture
async def db_session(
    async_session_maker: Callable[..., AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an AsyncSession instance for database operations in tests.

    Args:
    ----
    async_session_maker : Callable[..., AsyncSession]
        A session maker function that creates AsyncSession instances.

    Yields:
    ------
    AsyncSession
        An AsyncSession instance for use in tests.

    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# @pytest.fixture
# async def user_repository(db_session: AsyncSession) -> UserRepository:
#     """
#     Create and return a UserRepository instance for testing.

#     Args:
#     ----
#     db_session : AsyncSession
#         The async SQLAlchemy session.

#     Returns:
#     -------
#     UserRepository
#         An instance of UserRepository.

#     """
#     return UserRepository(db_session)


# @pytest.fixture
# async def test_user(user_repository: UserRepository) -> User:
#     """
#     Create and return a test user for testing.

#     Args:
#     ----
#     user_repository : UserRepository
#         The UserRepository instance.

#     Returns:
#     -------
#     User
#         The created test user.

#     """
#     user_data = UserCreate(
#         first_name="Test",
#         last_name="User",
#         email="test@example.com",
#         phone_number="+1234567890",
#         identities=[],
#     )
#     return await user_repository.create(user_data)
