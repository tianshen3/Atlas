from pathlib import Path
from uuid import uuid4
import fitz
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

# SQLite compiler compatibility helper for PostgreSQL JSONB columns in test environment
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from app.core.exceptions import ValidationException
from app.db.base import Base
from app.schemas.document import DocumentCreate, DocumentStatus
from app.services.document_service import DocumentService
from app.workers.pdf_processor import chunk_document_pages, extract_text_from_pdf


@pytest.fixture
async def db_session():
    """Fixture providing an async in-memory SQLite database session for integration testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.anyio
async def test_full_ingestion_pipeline(tmp_path: Path, db_session: AsyncSession):
    """Integration test verifying end-to-end PDF extraction, chunking, and database insertion."""
    # 1. Create a 2-page sample PDF on disk
    pdf_path = tmp_path / "integration_sample.pdf"
    doc = fitz.open()
    
    page1 = doc.new_page()
    page1.insert_text(
        (50, 50),
        "Atlas is an enterprise Retrieval-Augmented Generation platform built with FastAPI and Qdrant."
    )
    
    page2 = doc.new_page()
    page2.insert_text(
        (50, 50),
        "It supports dense vector embeddings, hybrid keyword search, and reciprocal rank fusion."
    )
    
    doc.save(str(pdf_path))
    doc.close()

    # 2. Step 1 of pipeline: Extract pages from PDF
    pages = extract_text_from_pdf(pdf_path)
    assert len(pages) == 2

    # 3. Step 2 of pipeline: Chunk document pages using token-aware sentence splitter
    chunks_data = chunk_document_pages(pages, chunk_size=100, chunk_overlap=10)
    assert len(chunks_data) >= 2

    # 4. Step 3 of pipeline: Register Document in DB
    doc_in = DocumentCreate(
        owner_id=None,
        filename="integration_sample.pdf",
        file_path=str(pdf_path),
        file_size_bytes=pdf_path.stat().st_size,
        mime_type="application/pdf",
        file_hash="test_sha256_hash",
    )
    db_doc = await DocumentService.create_document(db_session, doc_in)
    assert db_doc.status == DocumentStatus.PENDING.value

    # 5. Step 4 of pipeline: Save chunks to DB and verify status update
    saved_chunks = await DocumentService.save_chunks_to_db(db_session, db_doc.id, chunks_data)
    
    assert len(saved_chunks) == len(chunks_data)
    assert db_doc.status == DocumentStatus.COMPLETED.value
    
    # 6. Verify chunk properties in DB
    for idx, chunk in enumerate(saved_chunks):
        assert chunk.document_id == db_doc.id
        assert chunk.chunk_index == idx
        assert len(chunk.text) > 0
        assert chunk.token_count > 0
        assert "page_number" in chunk.metadata_json


@pytest.mark.anyio
async def test_save_chunks_to_db_nonexistent_document(db_session: AsyncSession):
    """Verify that saving chunks to a non-existent document ID raises a ValidationException."""
    non_existent_id = uuid4()
    chunks_data = [
        {"chunk_index": 0, "page_number": 1, "text": "Sample text", "token_count": 2}
    ]
    
    with pytest.raises(ValidationException) as exc_info:
        await DocumentService.save_chunks_to_db(db_session, non_existent_id, chunks_data)
        
    assert f"Document with id '{non_existent_id}' not found." in str(exc_info.value.message)
