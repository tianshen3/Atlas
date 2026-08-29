import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.deps import get_chat_service
from app.schemas.chat import ChatResponse


@pytest.mark.asyncio
async def test_ask_chat_endpoint_success():
    mock_service = AsyncMock()
    mock_service.generate_chat_response.return_value = ChatResponse(
        query="What is ATLAS?",
        answer="ATLAS is an Enterprise Hybrid RAG platform.",
        sources=[],
        model_used="meta-llama/llama-3.3-70b-instruct:free",
        provider_used="openrouter",
        total_sources=0,
    )

    app.dependency_overrides[get_chat_service] = lambda: mock_service

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            payload = {"query": "What is ATLAS?", "tenant_id": "tenant_123"}
            response = await client.post("/api/v1/chat/ask", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "What is ATLAS?"
            assert data["answer"] == "ATLAS is an Enterprise Hybrid RAG platform."
            assert data["model_used"] == "meta-llama/llama-3.3-70b-instruct:free"
            mock_service.generate_chat_response.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_stream_chat_completions_endpoint_success():
    async def mock_stream_generator(*args, **kwargs):
        yield "data: {\"event\": \"sources\", \"data\": []}\n\n"
        yield "data: {\"event\": \"token\", \"data\": \"ATLAS \"}\n\n"
        yield "data: {\"event\": \"token\", \"data\": \"is active.\"}\n\n"

    mock_service = MagicMock()
    mock_service.generate_chat_response_stream.side_effect = mock_stream_generator

    app.dependency_overrides[get_chat_service] = lambda: mock_service

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            payload = {"query": "What is ATLAS?", "tenant_id": "tenant_123"}
            response = await client.post("/api/v1/chat/completions", json=payload)

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            body = response.text
            assert "sources" in body
            assert "ATLAS " in body
            assert "is active." in body
    finally:
        app.dependency_overrides.clear()
