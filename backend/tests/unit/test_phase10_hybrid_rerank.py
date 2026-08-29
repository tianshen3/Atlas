import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from qdrant_client.models import ScoredPoint
from app.rag.embeddings import SparseEmbeddingEngine
from app.rag.reranker import compute_rrf, CrossEncoderReranker
from app.services.retrieval_service import RetrievalService
from app.schemas.retrieval import SearchRequest


def test_sparse_embedding_engine():
    with patch("app.rag.embeddings.SparseTextEmbedding") as MockSparse:
        mock_instance = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.indices = [1, 5, 10]
        mock_embedding.values = [0.5, 1.2, 0.8]
        mock_instance.embed.return_value = iter([mock_embedding])
        MockSparse.return_value = mock_instance

        engine = SparseEmbeddingEngine()
        result = engine.embed_query("test query")
        assert result.indices == [1, 5, 10]
        assert result.values == [0.5, 1.2, 0.8]


def test_sparse_embedding_engine_empty():
    engine = SparseEmbeddingEngine.__new__(SparseEmbeddingEngine)
    assert engine.embed_documents([]) == []
    with pytest.raises(ValueError):
        engine.embed_query("   ")


def test_compute_rrf_scoring():
    point1 = ScoredPoint(id="p1", score=0.9, payload={"content": "doc1"}, version=1)
    point2 = ScoredPoint(id="p2", score=0.8, payload={"content": "doc2"}, version=1)
    point3 = ScoredPoint(id="p3", score=0.7, payload={"content": "doc3"}, version=1)

    dense_hits = [point1, point2]
    sparse_hits = [point2, point3]

    fusion_results = compute_rrf(dense_hits, sparse_hits, k=60)
    assert len(fusion_results) == 3

    # point2 is in both: rank 2 in dense (1/(60+2)) + rank 1 in sparse (1/(60+1))
    p2_score = (1.0 / 62.0) + (1.0 / 61.0)
    assert fusion_results[0][0].id == "p2"
    assert pytest.approx(fusion_results[0][1], 0.0001) == p2_score


def test_cross_encoder_reranker():
    reranker = CrossEncoderReranker()
    reranker._model = MagicMock()
    reranker._model.predict.return_value = [0.15, 0.92]

    p1 = ScoredPoint(id="p1", score=0.5, payload={"content": "alpha"}, version=1)
    p2 = ScoredPoint(id="p2", score=0.6, payload={"content": "beta"}, version=1)

    reranked = reranker.rerank("query", [p1, p2], top_k=2)
    assert len(reranked) == 2
    assert reranked[0][0].id == "p2"
    assert reranked[0][1] == 0.92
    assert reranked[1][0].id == "p1"
    assert reranked[1][1] == 0.15


@pytest.mark.asyncio
async def test_retrieval_service_hybrid_search():
    mock_dense = MagicMock()
    mock_dense.embed_query.return_value = [0.1] * 384

    mock_sparse = MagicMock()
    mock_sparse_vec = MagicMock()
    mock_sparse_vec.indices = [1, 2]
    mock_sparse_vec.values = [0.5, 0.5]
    mock_sparse.embed_query.return_value = mock_sparse_vec

    mock_qdrant = AsyncMock()
    p1 = ScoredPoint(id="12345678-1234-5678-1234-567812345678", score=0.8, payload={"document_id": "87654321-4321-8765-4321-876543218765", "content": "test"}, version=1)
    mock_qdrant.search_vectors.return_value = [p1]

    service = RetrievalService(
        embedding_engine=mock_dense,
        sparse_embedding_engine=mock_sparse,
        qdrant_service=mock_qdrant,
    )

    request = SearchRequest(query="test", tenant_id="tenant_1", top_k=1)
    response = await service.search(request, enable_hybrid=True)


    assert response.total_results == 1
    assert str(response.results[0].chunk_id) == "12345678-1234-5678-1234-567812345678"
