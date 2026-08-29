from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()

@router.get("/healthz", response_model = HealthResponse)
async def health_check() -> HealthResponse:

    #serivce health endpoint
    return HealthResponse(
        status = "HEALTHY",
        version = settings.VERSION,
        components = {
            "api" : "UP",
        },
    )

