from app.api.v1.api import api_router
from app.core.config import settings
from fastapi  import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions import (
    AtlasException,
    atlas_exception_handler,
    global_exception_handler,
)

#application factory
def create_application() -> FastAPI:
    app = FastAPI(
        title = settings.PROJECT_NAME,
        version = settings.VERSION,
        openapi_url = f"{settings.API_V1_STR}/openapi.json",
        docs_url = f"{settings.API_V1_STR}/docs",
        redoc_url = f"{settings.API_V1_STR}/redocs",
    )

    # configuring cors middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # register custom exception handles
    app.add_exception_handler(AtlasException, atlas_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # root health check endpoint for cloud load balancers and Render
    @app.get("/health", tags=["Health"])
    async def root_health_check():
        return {"status": "HEALTHY", "version": settings.VERSION}

    # mounting v1 api router
    app.include_router(api_router, prefix = settings.API_V1_STR)

    return app

app = create_application()