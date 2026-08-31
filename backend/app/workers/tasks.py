"""
Celery background worker tasks for asynchronous PDF ingestion.
"""

import asyncio
import structlog

from app.workers.celery_app import celery_app
from app.workers.pipeline import mark_document_failed, run_ingestion_pipeline

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_document_task(self, document_id: str, file_path: str, tenant_id: str) -> dict:
    """
    Celery background task: runs the full ingestion pipeline via asyncio.run().

    Args:
        document_id: UUID string of the document record.
        file_path: Absolute local path of the stored PDF.
        tenant_id: Tenant identifier for Qdrant payload isolation.
    """
    logger.info(
        "processing_document_task_started",
        document_id=document_id,
        file_path=file_path,
        tenant_id=tenant_id,
    )

    try:
        total_chunks = asyncio.run(
            run_ingestion_pipeline(document_id, file_path, tenant_id)
        )
        logger.info(
            "processing_document_task_completed",
            document_id=document_id,
            total_chunks=total_chunks,
        )
        return {
            "status": "SUCCESS",
            "document_id": document_id,
            "tenant_id": tenant_id,
            "total_chunks": total_chunks,
        }

    except Exception as exc:
        logger.error(
            "processing_document_task_failed",
            document_id=document_id,
            error=str(exc),
        )
        asyncio.run(mark_document_failed(document_id, error=str(exc)))
        raise self.retry(exc=exc)
