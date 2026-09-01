"""
Shared async ingestion pipeline.
Used by the Celery task (via asyncio.run) AND as a FastAPI BackgroundTask
fallback when Redis/Celery is unavailable.
"""

import structlog
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from app.rag.embeddings import DenseEmbeddingEngine
from app.rag.qdrant import QdrantVectorService
from app.services.document_service import DocumentService
from app.workers.pdf_processor import chunk_document_pages, extract_text_from_pdf

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def _get_embedding_engine() -> DenseEmbeddingEngine:
    """Module-level singleton — ONNX model is loaded once and reused for all uploads."""
    logger.info("pipeline_initializing_embedding_engine")
    return DenseEmbeddingEngine()


@lru_cache(maxsize=1)
def _get_qdrant_service() -> QdrantVectorService:
    """Module-level singleton — Qdrant client connection is shared across uploads."""
    logger.info("pipeline_initializing_qdrant_service")
    return QdrantVectorService()



async def run_ingestion_pipeline(
    document_id: str,
    file_path: str,
    tenant_id: str = "tenant_default",
) -> int:
    """
    Full async ingestion pipeline shared by Celery worker and FastAPI background fallback.

    Steps:
        1. Extract text from PDF via PyMuPDF.
        2. Chunk pages via LlamaIndex SentenceSplitter.
        3. Mark document status → PROCESSING.
        4. Generate 384-dim dense embeddings via FastEmbed.
        5. Persist chunks to Postgres.
        6. Upsert vectors to Qdrant with correct payload schema.
        7. Mark document status → COMPLETED.

    Returns:
        Total number of chunks produced.

    Raises:
        Any exception propagates to the caller (Celery retry / background task error log).
    """
    from sqlalchemy import select

    from app.db.models.document import Document
    from app.db.session import AsyncSessionLocal

    doc_uuid = UUID(document_id)

    # Derive original filename — strip UUID prefix added during upload
    # Storage format: "{uuid}_{original_filename}"
    raw_name = Path(file_path).name
    parts = raw_name.split("_", 1)
    original_filename = parts[1] if len(parts) > 1 else raw_name

    # Step 1 & 2: Extract and chunk (CPU-bound, sync)
    pages = extract_text_from_pdf(file_path)
    chunks = chunk_document_pages(pages)

    logger.info(
        "pipeline_extracted_and_chunked",
        document_id=document_id,
        total_chunks=len(chunks),
    )

    # Step 3: Mark PROCESSING
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == doc_uuid))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "PROCESSING"
            await db.commit()

    # Step 4-7: Embed → Postgres → Qdrant → COMPLETED
    # Use module-level singletons — ONNX model loaded ONCE at startup, not per-upload
    embedding_engine = _get_embedding_engine()
    qdrant_service = _get_qdrant_service()

    # Verify Qdrant connectivity before embedding — surface errors early in logs
    try:
        collection_info = await qdrant_service.client.get_collection("atlas_chunks_v1")
        logger.info(
            "qdrant_collection_verified",
            points_count=collection_info.points_count,
            vector_size=collection_info.config.params.vectors.size,
        )
    except Exception as qdrant_err:
        logger.error(
            "qdrant_connection_failed_before_embed",
            document_id=document_id,
            error=str(qdrant_err),
        )
        raise  # Propagates to mark_document_failed in the caller

    async with AsyncSessionLocal() as db:
        try:
            saved_chunks = await DocumentService.save_chunks_to_db(
                db=db,
                document_id=doc_uuid,
                chunks_data=chunks,
                qdrant_service=qdrant_service,
                embedding_engine=embedding_engine,
                collection_name="atlas_chunks_v1",
                tenant_id=tenant_id,
                filename=original_filename,
            )
            qdrant_ids = [c.qdrant_point_id for c in saved_chunks]
            logger.info(
                "pipeline_completed",
                document_id=document_id,
                total_chunks=len(saved_chunks),
                qdrant_points_stored=len([q for q in qdrant_ids if q]),
            )
        except Exception as embed_err:
            logger.error(
                "pipeline_embed_or_upsert_failed",
                document_id=document_id,
                error=str(embed_err),
            )
            raise  # Propagates to mark_document_failed in the caller

    return len(chunks)


async def mark_document_failed(document_id: str, error: str = "") -> None:
    """Best-effort: set document status to FAILED and record the error message."""
    from sqlalchemy import select

    from app.db.models.document import Document
    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Document).where(Document.id == UUID(document_id))
            )
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "FAILED"
                doc.error_message = error or "Unknown error during ingestion."
                await db.commit()
    except Exception as e:
        logger.warning("mark_document_failed_error", document_id=document_id, error=str(e))
