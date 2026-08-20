import pytest
from unittest.mock import AsyncMock, patch
from qdrant_client.models import PointStruct, ScoredPoint
from app.rag.qdrant import QdrantVectorService


@pytest.mark.asyncio
async def test_qdrant_service_initialization():
    service = QdrantVectorService(host="localhost", port=6333)
    assert service.host == "localhost"
    assert service.port == 6333
    await service.close()


@pytest.mark.asyncio
async def test_init_collection_creates_when_not_exists():
    with patch("app.rag.qdrant.AsyncQdrantClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.collection_exists.return_value = False
        MockClient.return_value = mock_instance

        service = QdrantVectorService()
        await service.init_collection("test_collection", vector_size=384)

        mock_instance.collection_exists.assert_called_once_with("test_collection")
        mock_instance.create_collection.assert_called_once()
        assert mock_instance.create_payload_index.call_count == 2


@pytest.mark.asyncio
async def test_init_collection_skips_when_exists():
    with patch("app.rag.qdrant.AsyncQdrantClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.collection_exists.return_value = True
        MockClient.return_value = mock_instance

        service = QdrantVectorService()
        await service.init_collection("test_collection", vector_size=384)

        mock_instance.collection_exists.assert_called_once_with("test_collection")
        mock_instance.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_chunk_vectors():
    with patch("app.rag.qdrant.AsyncQdrantClient") as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value = mock_instance

        service = QdrantVectorService()
        points = [
            PointStruct(id="12345678-1234-5678-1234-567812345678", vector=[0.1] * 384, payload={"text": "hello"})
        ]
        await service.upsert_chunk_vectors("test_collection", points)

        mock_instance.upsert.assert_called_once_with(
            collection_name="test_collection",
            points=points,
        )


@pytest.mark.asyncio
async def test_upsert_empty_points_list():
    with patch("app.rag.qdrant.AsyncQdrantClient") as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value = mock_instance

        service = QdrantVectorService()
        await service.upsert_chunk_vectors("test_collection", [])

        mock_instance.upsert.assert_not_called()


@pytest.mark.asyncio
async def test_search_vectors_with_tenant_only():
    with patch("app.rag.qdrant.AsyncQdrantClient") as MockClient:
        mock_instance = AsyncMock()
        expected_results = [
            ScoredPoint(id="12345678-1234-5678-1234-567812345678", score=0.92, payload={"text": "hello"}, version=1)
        ]
        mock_instance.search.return_value = expected_results
        MockClient.return_value = mock_instance

        service = QdrantVectorService()
        query_vec = [0.1] * 384
        results = await service.search_vectors(
            collection_name="test_collection",
            query_vector=query_vec,
            tenant_id="tenant_123",
        )

        assert results == expected_results
        mock_instance.search.assert_called_once()
        call_kwargs = mock_instance.search.call_args.kwargs
        assert call_kwargs["collection_name"] == "test_collection"
        assert call_kwargs["query_vector"] == query_vec
        assert call_kwargs["limit"] == 5
        assert call_kwargs["score_threshold"] is None
        assert call_kwargs["with_payload"] is True
        filter_obj = call_kwargs["query_filter"]
        assert len(filter_obj.must) == 1
        assert filter_obj.must[0].key == "tenant_id"
        assert filter_obj.must[0].match.value == "tenant_123"


@pytest.mark.asyncio
async def test_search_vectors_with_document_filter_and_score_threshold():
    with patch("app.rag.qdrant.AsyncQdrantClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.search.return_value = []
        MockClient.return_value = mock_instance

        service = QdrantVectorService()
        query_vec = [0.1] * 384
        results = await service.search_vectors(
            collection_name="test_collection",
            query_vector=query_vec,
            tenant_id="tenant_123",
            document_id="doc_abc",
            limit=10,
            score_threshold=0.75,
        )

        assert results == []
        mock_instance.search.assert_called_once()
        call_kwargs = mock_instance.search.call_args.kwargs
        assert call_kwargs["limit"] == 10
        assert call_kwargs["score_threshold"] == 0.75
        filter_obj = call_kwargs["query_filter"]
        assert len(filter_obj.must) == 2
        assert filter_obj.must[0].key == "tenant_id"
        assert filter_obj.must[0].match.value == "tenant_123"
        assert filter_obj.must[1].key == "document_id"
        assert filter_obj.must[1].match.value == "doc_abc"

