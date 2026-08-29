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
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # register custom exception handles
    app.add_exception_handler(AtlasException, atlas_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # mountin v1 api router
    app.include_router(api_router, prefix = settings.API_V1_STR)

    return app

app = create_application()