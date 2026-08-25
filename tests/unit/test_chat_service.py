import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.retrieval import SearchResponse, SearchResultChunk
from app.services.chat_service import ChatService


@pytest.mark.asyncio
async def test_chat_service_generate_response_success():
    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    mock_chunk = SearchResultChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        chunk_index=0,
        content="ATLAS uses FastAPI and Qdrant for RAG.",
        score=0.94,
        metadata={"file_name": "atlas_arch.pdf", "page_number": 3},
    )

    mock_retrieval = AsyncMock()
    mock_retrieval.search.return_value = SearchResponse(
        query="What tech stack does ATLAS use?",
        results=[mock_chunk],
        total_results=1,
    )

    mock_generator = AsyncMock()
    mock_generator.default_model = "meta-llama/llama-3.3-70b-instruct:free"
    mock_generator.provider = "openrouter"
    mock_generator.generate_answer.return_value = (
        "ATLAS uses FastAPI and Qdrant for RAG [Source 1]."
    )

    service = ChatService(
        retrieval_service=mock_retrieval,
        generator_engine=mock_generator,
    )

    request = ChatRequest(
        query="What tech stack does ATLAS use?",
        tenant_id="tenant_123",
        top_k=5,
    )

    response = await service.generate_chat_response(request)

    assert isinstance(response, ChatResponse)
    assert response.query == "What tech stack does ATLAS use?"
    assert response.answer == "ATLAS uses FastAPI and Qdrant for RAG [Source 1]."
    assert response.model_used == "meta-llama/llama-3.3-70b-instruct:free"
    assert response.provider_used == "openrouter"
    assert len(response.sources) == 1
    assert response.sources[0].file_name == "atlas_arch.pdf"
    assert response.sources[0].page_number == 3

    mock_retrieval.search.assert_called_once()
    mock_generator.generate_answer.assert_called_once()


@pytest.mark.asyncio
async def test_chat_service_empty_retrieval_short_circuit():
    mock_retrieval = AsyncMock()
    mock_retrieval.search.return_value = SearchResponse(
        query="Unrelated topic",
        results=[],
        total_results=0,
    )

    mock_generator = AsyncMock()
    mock_generator.default_model = "meta-llama/llama-3.3-70b-instruct:free"
    mock_generator.provider = "openrouter"

    service = ChatService(
        retrieval_service=mock_retrieval,
        generator_engine=mock_generator,
    )

    request = ChatRequest(
        query="Unrelated topic",
        tenant_id="tenant_123",
    )

    response = await service.generate_chat_response(request)

    assert "cannot find sufficient information" in response.answer
    assert response.sources == []
    assert response.total_sources == 0

    # Ensure LLM generator was NOT invoked when retrieval was empty
    mock_generator.generate_answer.assert_not_called()
