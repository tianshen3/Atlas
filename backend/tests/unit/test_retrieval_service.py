import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from qdrant_client.models import ScoredPoint

from app.schemas.retrieval import SearchRequest, SearchResponse
from app.services.retrieval_service import RetrievalService


@pytest.mark.asyncio
async def test_retrieval_service_search_success():
    # Arrange mock embedding engine and mock qdrant service
    mock_embedding_engine = MagicMock()
    mock_embedding_engine.embed_query.return_value = [0.1] * 384

    doc_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    mock_qdrant = AsyncMock()
    mock_scored_point = ScoredPoint(
        id=str(chunk_id),
        version=1,
        score=0.92,
        payload={
            "document_id": str(doc_id),
            "chunk_index": 0,
            "content": "Test retrieval snippet.",
            "tenant_id": "tenant_abc",
        },
        vector=None,
    )
    mock_qdrant.search_vectors.return_value = [mock_scored_point]

    service = RetrievalService(
        embedding_engine=mock_embedding_engine,
        qdrant_service=mock_qdrant,
    )

    request = SearchRequest(
        query="What is Atlas platform?",
        tenant_id="tenant_abc",
        top_k=5,
    )

    # Act
    response = await service.search(request)

    # Assert
    assert isinstance(response, SearchResponse)
    assert response.query == "What is Atlas platform?"
    assert response.total_results == 1
    assert len(response.results) == 1

    chunk = response.results[0]
    assert chunk.chunk_id == chunk_id
    assert chunk.document_id == doc_id
    assert chunk.content == "Test retrieval snippet."
    assert chunk.score == 0.92

    mock_embedding_engine.embed_query.assert_called_once_with("What is Atlas platform?")
    mock_qdrant.search_vectors.assert_called_once_with(
        collection_name="atlas_chunks_v1",
        query_vector=[0.1] * 384,
        tenant_id="tenant_abc",
        document_id=None,
        limit=5,
    )


@pytest.mark.asyncio
async def test_retrieval_service_missing_tenant_id_raises_value_error():
    service = RetrievalService(
        embedding_engine=MagicMock(),
        qdrant_service=AsyncMock(),
    )
    request = SearchRequest(query="Test", tenant_id="", top_k=5)

    with pytest.raises(ValueError, match="tenant_id is required"):
        await service.search(request)
