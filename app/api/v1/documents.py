from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    """Accept PDF binary file upload, validate bytes, store to disk, and save PENDING record in DB."""
    file_name = file.filename or "upload.pdf"
    file_bytes = await file.read()

    # Validate PDF format and file size limits
    DocumentService.validate_pdf_file(file_bytes, file_name)

    # Compute SHA256 checksum and persist file to disk
    file_hash = DocumentService.compute_sha256(file_bytes)
    file_path = DocumentService.save_file_to_disk(file_bytes, file_name)

    # Prepare DB schema payload
    doc_in = DocumentCreate(
        filename=file_name,
        mime_type=file.content_type or "application/pdf",
        file_path=file_path,
        file_size_bytes=len(file_bytes),
        file_hash=file_hash,
        owner_id=None,
    )

    # Persist document record into PostgreSQL
    db_doc = await DocumentService.create_document(db, doc_in)
    return db_doc


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> DocumentListResponse:
    """Fetch paginated list of documents."""
    items, total = await DocumentService.list_documents(db, skip=skip, limit=limit)
    return DocumentListResponse(items=items, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> DocumentResponse:
    """Fetch a single document by UUID."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete document from database and unlink file from disk."""
    success = await DocumentService.delete_document(db, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
