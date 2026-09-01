"""
Documents REST Router.
"""

import structlog
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, get_qdrant_service
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

    # Deduplication check: if an identical file already exists, return it immediately
    existing_doc = await DocumentService.get_document_by_checksum(db, file_hash)
    if existing_doc:
        logger.info(
            "duplicate_document_upload_skipped",
            document_id=str(existing_doc.id),
            checksum=file_hash,
        )
        return existing_doc

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

    # Purge any stale FAILED/PROCESSING records with the same file so re-uploads work cleanly
    from sqlalchemy import select as _select
    from app.db.models.document import Document as _Doc
    stale_result = await db.execute(
        _select(_Doc).where(
            _Doc.checksum == file_hash,
            _Doc.status.in_(["FAILED", "PROCESSING"]),
        )
    )
    for stale in stale_result.scalars().all():
        logger.info("purging_stale_document", document_id=str(stale.id), status=stale.status)
        await db.delete(stale)
    await db.commit()

    db_doc = await DocumentService.create_document(db, doc_in)
    doc_id = str(db_doc.id)

    # Execute ingestion pipeline via FastAPI BackgroundTasks
    async def _inline_pipeline() -> None:
        try:
            await run_ingestion_pipeline(doc_id, file_path, "tenant_default")
        except Exception as exc:
            logger.error("inline_pipeline_failed", document_id=doc_id, error=str(exc))
            await mark_document_failed(doc_id)

    background_tasks.add_task(_inline_pipeline)
    logger.info("background_ingestion_task_queued", document_id=doc_id)

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
    qdrant_service=Depends(get_qdrant_service),
):
    """Delete document record, its disk file, and all associated Qdrant embeddings."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{document_id}' not found.")

    if current_user["role"] != "admin" and str(doc.owner_id) != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    await DocumentService.delete_document(db, document_id, qdrant_service=qdrant_service)
