from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query string")
    top_k: int = Field(default=5, ge=1, le=100, description="Maximum number of chunks to retrieve")
    tenant_id: Optional[str] = Field(default=None, description="Optional tenant identifier for isolated retrieval")
    document_id: Optional[UUID] = Field(default=None, description="Optional document ID filter")


class SearchResultChunk(BaseModel):
    chunk_id: UUID = Field(..., description="Unique identifier of the chunk point")
    document_id: UUID = Field(..., description="Unique identifier of the parent document")
    chunk_index: int = Field(..., description="Position of the chunk within the document")
    content: str = Field(..., description="Raw text content of the chunk")
    score: float = Field(..., description="Cosine similarity score calculated by Qdrant")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional chunk payload metadata")

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    query: str = Field(..., description="Original search query executed")
    results: List[SearchResultChunk] = Field(default_factory=list, description="Top matching chunk results")
    total_results: int = Field(..., description="Count of retrieved chunk results")
