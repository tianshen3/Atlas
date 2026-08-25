import uuid
import pytest
from app.schemas.retrieval import SearchResultChunk
from app.rag.prompts import format_context_block, build_grounded_messages


def test_format_context_block():
    doc_id = uuid.uuid4()
    chunk1 = SearchResultChunk(
        chunk_id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,
        content="ATLAS is an enterprise RAG platform.",
        score=0.95,
        metadata={"file_name": "atlas_doc.pdf", "page_number": 1},
    )
    chunk2 = SearchResultChunk(
        chunk_id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=1,
        content="It supports dense retrieval and vector search.",
        score=0.88,
        metadata={"file_name": "atlas_doc.pdf", "page_number": 2},
    )

    formatted = format_context_block([chunk1, chunk2])

    assert "[Source 1]" in formatted
    assert f"Document ID: {doc_id}" in formatted
    assert "File Name: atlas_doc.pdf" in formatted
    assert "Page Number: 1" in formatted
    assert "ATLAS is an enterprise RAG platform." in formatted

    assert "[Source 2]" in formatted
    assert "Page Number: 2" in formatted
    assert "It supports dense retrieval and vector search." in formatted


def test_build_grounded_messages():
    doc_id = uuid.uuid4()
    chunk = SearchResultChunk(
        chunk_id=uuid.uuid4(),
        document_id=doc_id,
        chunk_index=0,
        content="Qdrant is used as the vector database.",
        score=0.91,
        metadata={"file_name": "qdrant_info.pdf", "page_number": 5},
    )

    query = "Which vector database is used?"
    messages = build_grounded_messages(query, [chunk])

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    system_content = messages[0]["content"]
    assert "<context>" in system_content
    assert "</context>" in system_content
    assert "[Source 1]" in system_content
    assert "Qdrant is used as the vector database." in system_content
    assert messages[1]["content"] == query
