from fastapi import APIRouter
from app.api.v1 import auth, chat, documents, health, retrieval, tasks

# central router file for all the api v1 routes

api_router = APIRouter()
api_router.include_router(health.router, tags=["Healthz"])
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(retrieval.router)
api_router.include_router(chat.router)
api_router.include_router(tasks.router)

