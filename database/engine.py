import logging

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool

from database.config import get_database_settings

logger = logging.getLogger(__name__)

settings = get_database_settings()
engine = create_async_engine(
    settings.database_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=8,  # Optimized based on analysis
    max_overflow=10,  # Additional connections for traffic spikes
    pool_timeout=30,  # 30 seconds timeout (avg connection time is 0.29s)
    pool_recycle=1800,  # 30 minutes, recycle before Supabase timeout
    pool_pre_ping=True,  # Enable connection health checks
)


# # Add event listeners for connection pool events
# @event.listens_for(engine.sync_engine, "checkout")
# def receive_checkout(dbapi_connection, connection_record, connection_proxy):
#     logger.debug("Database connection checked out from pool")


# @event.listens_for(engine.sync_engine, "checkin")
# def receive_checkin(dbapi_connection, connection_record):
#     logger.debug("Database connection returned to pool")


# @event.listens_for(engine.sync_engine, "connect")
# def receive_connect(dbapi_connection, connection_record):
#     logger.info("New database connection created")


# @event.listens_for(engine.sync_engine, "reset")
# def receive_reset(dbapi_connection, connection_record):
#     logger.debug("Database connection reset")
