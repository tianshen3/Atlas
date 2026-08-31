"""
Documents REST Router.
"""

import structlog
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentResponse
from app.services.document_service import DocumentService
from app.workers.pipeline import mark_document_failed, run_ingestion_pipeline

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> DocumentResponse:
    """
    Accept PDF upload, validate, store to disk, create PENDING DB record,
    and enqueue ingestion via Celery. Falls back to FastAPI BackgroundTasks
    automatically if Celery/Redis is not available.
    """
    file_name = file.filename or "upload.pdf"
    file_bytes = await file.read()

    # Validate PDF format and file size
    DocumentService.validate_pdf_file(file_bytes, file_name)

    # SHA-256 checksum + persist to disk
    file_hash = DocumentService.compute_sha256(file_bytes)
    file_path = DocumentService.save_file_to_disk(file_bytes, file_name)

    # Build DB payload — set owner from authenticated user
    doc_in = DocumentCreate(
        filename=file_name,
        mime_type=file.content_type or "application/pdf",
        file_path=file_path,
        file_size_bytes=len(file_bytes),
        file_hash=file_hash,
        owner_id=UUID(current_user["id"]),
    )

    db_doc = await DocumentService.create_document(db, doc_in)
    doc_id = str(db_doc.id)

    # Attempt Celery dispatch; fall back to in-process BackgroundTask if unavailable
    celery_dispatched = False
    try:
        from app.workers.tasks import process_document_task
        process_document_task.delay(
            document_id=doc_id,
            file_path=file_path,
            tenant_id="tenant_default",
        )
        celery_dispatched = True
        logger.info("celery_task_dispatched", document_id=doc_id)
    except Exception as celery_exc:
        logger.warning(
            "celery_dispatch_failed_using_background_task",
            document_id=doc_id,
            error=str(celery_exc),
        )

    if not celery_dispatched:
        async def _inline_pipeline() -> None:
            try:
                await run_ingestion_pipeline(doc_id, file_path, "tenant_default")
            except Exception as exc:
                logger.error("inline_pipeline_failed", document_id=doc_id, error=str(exc))
                await mark_document_failed(doc_id)

        background_tasks.add_task(_inline_pipeline)

    return db_doc


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> DocumentListResponse:
    """
    Fetch paginated documents. Admins see all documents; regular users see only their own.
    """
    owner_id = None if current_user["role"] == "admin" else UUID(current_user["id"])
    items, total = await DocumentService.list_documents(db, skip=skip, limit=limit, owner_id=owner_id)
    return DocumentListResponse(items=items, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
) -> DocumentResponse:
    """Fetch a single document by UUID. Non-admins can only access their own documents."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")

    if current_user["role"] != "admin" and str(doc.owner_id) != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
):
    """Delete document. Non-admins can only delete their own documents."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")

    if current_user["role"] != "admin" and str(doc.owner_id) != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    await DocumentService.delete_document(db, document_id)
