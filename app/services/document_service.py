import hashlib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.db.models.document import Chunk, Document
from app.schemas.document import DocumentCreate, DocumentStatus

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limits
PDF_MAGIC_BYTES = b"%PDF"


class DocumentService:
    """Business service handling document binary validation, disk storage, and database persistence."""

    @staticmethod
    def validate_pdf_file(file_content: bytes, filename: str) -> None:
        """Validate PDF binary size and magic header bytes."""
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            raise ValidationException(
                message=f"File '{filename}' exceeds maximum allowed size of 50MB.",
                details={"filename": filename, "size_bytes": len(file_content)},
            )

        if not file_content.startswith(PDF_MAGIC_BYTES):
            raise ValidationException(
                message=f"File '{filename}' is not a valid PDF document (missing PDF magic header).",
                details={"filename": filename},
            )

    @staticmethod
    def compute_sha256(file_content: bytes) -> str:
        """Compute hex-encoded SHA-256 hash digest of file binary content."""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def save_file_to_disk(
        file_content: bytes, filename: str, storage_dir: str = "storage/documents"
    ) -> str:
        """Save raw binary content to disk with a unique UUID filename prefix."""
        target_dir = Path(storage_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        unique_filename = f"{uuid4()}_{filename}"
        file_path = target_dir / unique_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path)

    @staticmethod
    async def create_document(db: AsyncSession, doc_in: DocumentCreate) -> Document:
        """Persist a new Document record into PostgreSQL database."""
        db_doc = Document(
            owner_id=doc_in.owner_id,
            filename=doc_in.filename,
            file_path=doc_in.file_path,
            file_size=doc_in.file_size_bytes,
            mime_type=doc_in.mime_type,
            checksum=doc_in.file_hash,
            status=DocumentStatus.PENDING.value,
        )
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
        return db_doc

    @staticmethod
    async def get_document_by_id(
        db: AsyncSession, document_id: UUID
    ) -> Optional[Document]:
        """Fetch a single Document record by UUID from database."""
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        db: AsyncSession, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Document], int]:
        """Fetch a paginated list of Document records and total record count."""
        query = select(Document).offset(skip).limit(limit)
        result = await db.execute(query)
        items = list(result.scalars().all())

        count_query = select(func.count(Document.id))
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        return items, total
    
    @staticmethod
    async def delete_document(
        db: AsyncSession, document_id: UUID, delete_file_from_disk: bool = True) -> bool: 

        doc = await DocumentService.get_document_by_id(db, document_id)

        if not doc : return False

        if delete_file_from_disk and doc.file_path:
            p = Path(doc.file_path)
            if p.exists(): p.unlink()

        await db.delete(doc)
        await db.commit()
        return True

    @staticmethod
    async def save_chunks_to_db(
        db: AsyncSession, document_id: UUID, chunks_data: List[Dict[str, Any]]
    ) -> List[Chunk]:
        """Bulk insert extracted text chunks for a document into PostgreSQL and update status to PROCESSED."""
        doc = await DocumentService.get_document_by_id(db, document_id)
        if not doc:
            raise ValidationException(
                message=f"Document with id '{document_id}' not found.",
                details={"document_id": str(document_id)},
            )

        chunk_objects = [
            Chunk(
                document_id=document_id,
                chunk_index=chunk_info["chunk_index"],
                text=chunk_info["text"],
                token_count=chunk_info["token_count"],
                metadata_json={"page_number": chunk_info["page_number"]},
            )
            for chunk_info in chunks_data
        ]

        db.add_all(chunk_objects)
        doc.status = DocumentStatus.PROCESSED.value
        await db.commit()

        return chunk_objects

