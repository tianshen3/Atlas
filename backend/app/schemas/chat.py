from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    """Data Transfer Object for Chat generation requests."""
    query: str = Field(..., min_length=1, description="Natural language user question")
    document_id: Optional[UUID] = Field(default=None, description="Optional document ID filter for targeted grounding")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of context chunks to retrieve")
    model: Optional[str] = Field(default=None, description="Optional LLM model override")


class CitationSource(BaseModel):
    """Metadata DTO representing a cited chunk source."""
    source_index: int = Field(..., description="1-based citation index matching [Source X]")
    document_id: UUID = Field(..., description="Unique identifier of parent document")
    chunk_id: UUID = Field(..., description="Unique identifier of chunk")
    file_name: str = Field(default="Unknown", description="Source document file name")
    page_number: Any = Field(default="N/A", description="Page number within source document")
    score: float = Field(..., description="Cosine similarity score of chunk context")

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Structured response DTO containing grounded LLM answer and verified source citations."""
    query: str = Field(..., description="Original user query string")
    answer: str = Field(..., description="Grounded natural language answer synthesized by LLM")
    sources: List[CitationSource] = Field(default_factory=list, description="Verified source citations referenced in answer")
    model_used: str = Field(..., description="Specific LLM model used for completion")
    provider_used: str = Field(..., description="Inference provider used (e.g. openrouter)")
    total_sources: int = Field(..., description="Total count of context sources evaluated")
