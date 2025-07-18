# factory for creating app instances
import svcs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config.settings import settings
from dependency_injection import dependencies_registry, lifespan
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
    logger.info("FastAPI application created with CORS middleware configured.")

    return app
