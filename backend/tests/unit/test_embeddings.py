import pytest
from app.rag.embeddings import DenseEmbeddingEngine


@pytest.fixture(scope="module")
def embedding_engine():
    """Fixture providing a module-scoped instance of DenseEmbeddingEngine to avoid reloading model weights."""
    return DenseEmbeddingEngine()


def test_embed_documents_shape_and_type(embedding_engine: DenseEmbeddingEngine):
    """Test that embedding a list of document strings produces correct shape (N, 384) and float elements."""
    texts = [
        "Atlas RAG platform provides hybrid vector search.",
        "PostgreSQL and Qdrant store metadata and dense vectors.",
    ]
    vectors = embedding_engine.embed_documents(texts)

    assert isinstance(vectors, list)
    assert len(vectors) == 2

    for vec in vectors:
        assert isinstance(vec, list)
        assert len(vec) == 384
        assert all(isinstance(val, float) for val in vec)


def test_embed_query_shape_and_type(embedding_engine: DenseEmbeddingEngine):
    """Test that embedding a single query string produces a 384-dimensional vector."""
    query = "What database is used for vector search?"
    vector = embedding_engine.embed_query(query)

    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(val, float) for val in vector)


def test_embed_documents_empty_list(embedding_engine: DenseEmbeddingEngine):
    """Test that embedding an empty list of documents returns an empty list."""
    assert embedding_engine.embed_documents([]) == []


def test_embed_query_empty_string_raises_error(embedding_engine: DenseEmbeddingEngine):
    """Test that embedding an empty or whitespace-only query raises ValueError."""
    with pytest.raises(ValueError):
        embedding_engine.embed_query("")

    with pytest.raises(ValueError):
        embedding_engine.embed_query("    ")
