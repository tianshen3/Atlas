from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentBase(BaseModel):
    filename: str
    mime_type: str


class DocumentCreate(DocumentBase):
    file_path: str
    file_size_bytes: int
    file_hash: str
    owner_id: Optional[UUID] = None


class DocumentResponse(DocumentBase):
    id: UUID
    file_size_bytes: int = Field(validation_alias=AliasChoices("file_size_bytes", "file_size"))
    file_hash: str = Field(validation_alias=AliasChoices("file_hash", "checksum"))
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int


