"""
Celery background worker tasks for asynchronous PDF ingestion.
"""

import structlog
from app.workers.celery_app import celery_app
from app.workers.pdf_processor import extract_text_from_pdf, chunk_document_pages

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_document_task(self, document_id: str, file_path: str, tenant_id: str) -> dict:
    """
    Celery background task to extract text, chunk document, and prepare vector embeddings.

    Args:
        document_id: UUID string of the document.
        file_path: Local file path of the PDF.
        tenant_id: Tenant identifier for multi-tenant isolation.

    Returns:
        Task result payload dictionary.
    """
    logger.info("processing_document_task_started", document_id=document_id, file_path=file_path, tenant_id=tenant_id)
    try:
        pages = extract_text_from_pdf(file_path)
        chunks = chunk_document_pages(pages)
        logger.info("processing_document_task_completed", document_id=document_id, total_chunks=len(chunks))
        return {
            "status": "SUCCESS",
            "document_id": document_id,
            "tenant_id": tenant_id,
            "total_chunks": len(chunks),
        }
    except Exception as exc:
        logger.error("processing_document_task_failed", document_id=document_id, error=str(exc))
        raise self.retry(exc=exc)
