from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.engine import engine

Session = async_sessionmaker(bind=engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async session."""
    async with Session() as session:
        try:
            yield session
        finally:
            await session.close()
