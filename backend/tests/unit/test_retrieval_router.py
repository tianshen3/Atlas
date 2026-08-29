import uuid
import pytest
from unittest.mock import AsyncMock
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_retrieval_service
from app.services.retrieval_service import RetrievalService
from app.schemas.retrieval import SearchResponse, SearchResultChunk


@pytest.fixture
def client():
    return TestClient(app)


def test_search_endpoint_success(client):
    chunk_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    mock_response = SearchResponse(
        query="vector search test",
        results=[
            SearchResultChunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                chunk_index=0,
                content="Dense vector match text.",
                score=0.88,
                metadata=None,
            )
        ],
        total_results=1,
    )

    mock_service = AsyncMock()
    mock_service.search.return_value = mock_response

    app.dependency_overrides[get_retrieval_service] = lambda: mock_service

    payload = {
        "query": "vector search test",
        "tenant_id": "tenant_123",
        "top_k": 5,
    }

    response = client.post("/api/v1/retrieval/search", json=payload)
    app.dependency_overrides.clear()

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["query"] == "vector search test"
    assert data["total_results"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["content"] == "Dense vector match text."
    assert data["results"][0]["score"] == 0.88


def test_search_endpoint_missing_tenant_id(client):
    payload = {
        "query": "vector search test",
        "tenant_id": "",
        "top_k": 5,
    }

    response = client.post("/api/v1/retrieval/search", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "tenant_id is required" in response.json()["detail"]
