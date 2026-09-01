from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user, get_retrieval_service
from app.schemas.retrieval import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["Retrieval"])


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search_chunks(
    request: SearchRequest,
    service: RetrievalService = Depends(get_retrieval_service),
    current_user: dict = Depends(get_current_user),
) -> SearchResponse:
    """Execute dense vector similarity search across ingested document chunks."""
    # Inject tenant_id internally — not exposed in the API schema
    search_request = SearchRequest(
        query=request.query,
        top_k=request.top_k,
        document_id=request.document_id,
        tenant_id="tenant_default",
    )
    if not search_request.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id is required for isolated vector retrieval.",
        )
    try:
        return await service.search(search_request)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
