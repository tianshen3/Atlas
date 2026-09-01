from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import (
    AtlasException,
    atlas_exception_handler,
    global_exception_handler,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Startup: initialise Qdrant collection + payload indexes if not already present.
    Shutdown: nothing to clean up (connections managed per-request).
    """
    # Startup: initialise Qdrant collection + payload indexes
    try:
        from app.rag.qdrant import QdrantVectorService
        qs = QdrantVectorService()
        await qs.init_collection(collection_name="atlas_chunks_v1", vector_size=384, sparse=True)
        logger.info("Qdrant collection initialised on startup")
    except Exception as e:
        # Non-fatal: app still starts even if Qdrant is temporarily unavailable
        logger.warning("Qdrant init_collection failed on startup", error=str(e))

    yield
    # Shutdown (no teardown needed)



def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redocs",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom exception handlers
    app.add_exception_handler(AtlasException, atlas_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # Root health check for cloud load balancers
    @app.get("/health", tags=["Health"])
    async def root_health_check():
        return {"status": "HEALTHY", "version": settings.VERSION}

    # Mount versioned API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()