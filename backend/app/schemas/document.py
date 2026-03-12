from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DocumentMetadata(BaseModel):
    pages: Optional[int] = None
    checksum: Optional[str] = None
    encryption_key: Optional[str] = None
    tags: Optional[list] = None

class DocumentUpload(BaseModel):
    entity_id: int
    document_type: str
    metadata: Optional[DocumentMetadata] = None

class DocumentResponse(BaseModel):
    id: int
    entity_id: int
    document_type: str
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    upload_time: datetime
    uploaded_by: int
    version: int
    is_latest: bool
    metadata: Optional[str]

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
