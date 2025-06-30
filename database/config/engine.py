"""Database engine configuration with modern async patterns."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from common.config.settings import settings
from common.exceptions import AppError

logger = logging.getLogger(__name__)


class DatabaseError(AppError):
    """Database specific error."""

    status_code = 500
    detail = "Database operation failed"


class DatabaseSessionManager:
    """
    Modern database session manager for async SQLAlchemy.

    Handles connection pooling, session lifecycle, and graceful shutdown.
    """

    def __init__(self) -> None:
        """Initialize session manager."""
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    def init_db(self, database_url: str | None = None) -> None:
        """Initialize database engine and session maker."""
        url = database_url or str(settings.database.url)

        try:
            self._engine = create_async_engine(
                url,
                echo=settings.database.echo,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                pool_pre_ping=True,  # Verify connections before use
                pool_recycle=3600,  # Recycle connections after 1 hour
            )

            self._session_maker = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            logger.info("Database session manager initialized successfully")

        except Exception as e:
            logger.exception("Failed to initialize database: %s", e)
            msg = f"Database initialization failed: {e}"
            raise DatabaseError(msg) from e

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper error handling."""
        if self._session_maker is None:
            msg = "Database not initialized. Call init_db() first."
            raise DatabaseError(msg)

        async with self._session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.exception("Database session error: %s", e)
                msg = f"Database operation failed: {e}"
                raise DatabaseError(msg) from e
            finally:
                await session.close()

    async def create_tables(self) -> None:
        """Create all database tables."""
        if self._engine is None:
            msg = "Database engine not initialized"
            raise DatabaseError(msg)

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.exception("Failed to create tables: %s", e)
            msg = f"Table creation failed: {e}"
            raise DatabaseError(msg) from e

    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        if self._engine is None:
            msg = "Database engine not initialized"
            raise DatabaseError(msg)

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.exception("Failed to drop tables: %s", e)
            msg = f"Table drop failed: {e}"
            raise DatabaseError(msg) from e

    async def get_stats(self) -> dict[str, str]:
        """Get database connection statistics."""
        if self._engine is None:
            return {"status": "not_initialized"}

        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT version();"))
                version = result.fetchone()

                return {
                    "status": "connected",
                    "version": version[0] if version else "unknown",
                    "engine_url": str(self._engine.url).replace(self._engine.url.password, "***")
                    if self._engine.url.password
                    else str(self._engine.url),
                }

        except Exception as e:
            logger.exception("Failed to get database stats: %s", e)
            return {"status": "error", "message": str(e)}

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")


# Global session manager instance
sessionmanager = DatabaseSessionManager()


# Dependency for FastAPI
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    async with sessionmanager.get_session() as session:
        yield session
