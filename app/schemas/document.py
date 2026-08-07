from pydantic import ConfigDict
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from enum import Enum


class DocumentStatus(str, Enum):
    PENDING = "pending"
    IN_PROCESS = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentBase(BaseModel):
    filename:str
    mime_type: str

class DocumentCreate(DocumentBase):
    file_path: str
    file_size_bytes: int
    file_hash: str 
    owner_id: Optional[UUID]

class DocumentResponse(DocumentBase):
    id: UUID
    file_size_bytes: int
    file_hash: str
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int

