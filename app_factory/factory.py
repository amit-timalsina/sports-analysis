# factory for creating app instances
import svcs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.routers.login_router import router as login_router
from auth.routers.user_router import router as user_router
from common.config.settings import settings
from core_router.router.core_router import router as core_router
from dashboard.routers.dashboard_router import router as dashboard_router
from dependency_injection import dependencies_registry, lifespan
from fitness_tracking.routers.analytics_router import router as fitness_analytics_router
from fitness_tracking.routers.entries_router import router as fitness_entries_router
from logger import get_logger
from voice_processing.routers.audio_router import router as voice_audio_router
from voice_processing.routers.chat_message_router import router as message_router
from voice_processing.routers.conversation_router import router as conversation_router
from voice_processing.routers.session_router import router as voice_session_router

# from voice_processing.routers.websocket_router import router as voice_websocket_router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.

    Returns
    -------
        FastAPI: Configured FastAPI application instance.

    """
    app = FastAPI(
        title=settings.app.title,
        description=settings.app.description,
        version=settings.app.version,
        lifespan=svcs.fastapi.lifespan(lifespan=lifespan, registry=dependencies_registry),
        docs_url="/api/docs" if not settings.app.is_production else None,
        redoc_url="/api/redoc" if not settings.app.is_production else None,
        debug=settings.app.debug,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # set all routers
    setup_routes(app)

    logger.info("FastAPI application created with CORS middleware configured.")

    return app


def setup_routes(app: FastAPI) -> None:
    """Set up all application routers."""
    # include core router
    app.include_router(core_router)
    # include voice processing routers
    app.include_router(conversation_router)
    app.include_router(message_router)
    app.include_router(voice_audio_router)
    app.include_router(voice_session_router)
    # app.include_router(voice_websocket_router)
    # include dashboard router
    app.include_router(dashboard_router)
    # include fitness tracking routers
    app.include_router(fitness_entries_router)
    app.include_router(fitness_analytics_router)
    # include authentication routers
    app.include_router(login_router)
    app.include_router(user_router)
