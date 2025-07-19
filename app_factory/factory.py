# factory for creating app instances
import svcs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.analytics_router import router as analytics_router
from api.routers.audio_router import router as audio_router
from api.routers.core_router import router as core_router
from api.routers.dashboard_router import router as dashboard_router
from api.routers.entries_router import router as entries_router
from api.routers.session_router import router as session_router
from api.routers.websocket_router import router as websocket_router
from auth.routers.login import router as login_router
from auth.routers.user_router import router as user_router
from common.config.settings import settings
from dependency_injection import dependencies_registry, lifespan
from fitness_tracking.routers.activity_router import (
    cricket_coaching_router,
    cricket_match_router,
    fitness_router,
    rest_day_router,
)
from logger import get_logger

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
        docs_url="/api/docs" if not settings.app.is_production else None,  # type: ignore[truthy-function]
        redoc_url="/api/redoc" if not settings.app.is_production else None,  # type: ignore[truthy-function]
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
    # Core routes (no prefix)
    app.include_router(core_router)

    # Auth routers
    app.include_router(login_router)
    app.include_router(user_router, prefix="/api/auth")

    # # Include activity routers with /api prefix
    # app.include_router(fitness_router, prefix="/api")
    # app.include_router(rest_day_router, prefix="/api")
    # app.include_router(cricket_coaching_router, prefix="/api")
    # app.include_router(cricket_match_router, prefix="/api")
    # API routers
    app.include_router(session_router)
    app.include_router(audio_router)
    app.include_router(entries_router)
    app.include_router(analytics_router)
    app.include_router(dashboard_router)

    # WebSocket router
    app.include_router(websocket_router)
