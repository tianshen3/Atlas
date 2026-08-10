from fastapi import APIRouter
from app.api.v1 import documents, health

# central router file for all the api v1 routes

api_router = APIRouter()
api_router.include_router(health.router, tags=["Healthz"])
api_router.include_router(documents.router)