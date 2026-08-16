import pytest
from unittest.mock import AsyncMock, patch
from qdrant_client.models import PointStruct
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
