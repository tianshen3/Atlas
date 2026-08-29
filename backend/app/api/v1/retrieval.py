from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_retrieval_service
from app.schemas.retrieval import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_chunks(
    request: SearchRequest,
    service: RetrievalService = Depends(get_retrieval_service),
) -> SearchResponse:
    """Execute dense vector similarity search across ingested document chunks."""
    if not request.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id is required for isolated vector retrieval.",
        )
    try:
        return await service.search(request)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
