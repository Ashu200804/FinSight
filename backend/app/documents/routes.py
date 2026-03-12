from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.document import DocumentUpload, DocumentResponse, DocumentListResponse
from app.database.config import get_db
from app.storage.minio_client import upload_file, download_file, delete_file, list_files, ensure_bucket_exists
from app.utils.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
import json
from datetime import datetime
import io

router = APIRouter(prefix="/documents", tags=["documents"])
security = HTTPBearer()

# Ensure bucket exists when module loads
ensure_bucket_exists()

# Supported file types
SUPPORTED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
}

REQUIRED_DOCUMENTS = [
    'ALM',
    'Shareholding Pattern',
    'Borrowing Profile',
    'Annual Reports',
    'Portfolio Performance',
]

def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> int:
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return int(payload.get("sub"))

def validate_file_type(mime_type: str) -> bool:
    """Validate if file mime type is supported"""
    return mime_type in SUPPORTED_MIME_TYPES

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    entity_id: int = Form(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Upload a document to secure vault"""
    
    if not entity_id or not document_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="entity_id and document_type are required"
        )
    
    # Validate file type
    if not validate_file_type(file.content_type or "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Supported types: PDF, Excel, CSV, Images"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Check file size (max 100MB)
        if file_size > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 100MB limit"
            )
        
        # Mark previous versions as not latest
        db.query(Document).filter(
            Document.entity_id == entity_id,
            Document.document_type == document_type,
            Document.is_latest == "true"
        ).update({"is_latest": "false"})
        
        # Get next version number
        last_version = db.query(Document).filter(
            Document.entity_id == entity_id,
            Document.document_type == document_type,
        ).order_by(Document.version.desc()).first()
        
        next_version = (last_version.version + 1) if last_version else 1
        
        # Upload to MinIO
        object_path = upload_file(file_content, file.filename, entity_id, document_type)
        
        # Create document record
        new_document = Document(
            entity_id=entity_id,
            document_type=document_type,
            file_path=object_path,
            file_name=file.filename,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_by=user_id,
            version=next_version,
            is_latest="true",
            document_metadata=None
        )
        
        db.add(new_document)
        db.commit()
        db.refresh(new_document)
        
        return {
            "id": new_document.id,
            "entity_id": new_document.entity_id,
            "document_type": new_document.document_type,
            "file_path": new_document.file_path,
            "file_name": new_document.file_name,
            "file_size": new_document.file_size,
            "mime_type": new_document.mime_type,
            "upload_time": new_document.upload_time,
            "uploaded_by": new_document.uploaded_by,
            "version": new_document.version,
            "is_latest": new_document.is_latest == "true",
            "message": "Document uploaded successfully"
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/entity/{entity_id}")
def get_entity_documents(
    entity_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all documents for an entity"""
    
    documents = db.query(Document).filter(
        Document.entity_id == entity_id,
        Document.is_latest == "true"
    ).all()
    
    return {
        "entity_id": entity_id,
        "documents": [
            {
                "id": doc.id,
                "entity_id": doc.entity_id,
                "document_type": doc.document_type,
                "file_path": doc.file_path,
                "file_name": doc.file_name,
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
                "upload_time": doc.upload_time,
                "uploaded_by": doc.uploaded_by,
                "version": doc.version,
                "is_latest": doc.is_latest == "true",
                "metadata": doc.document_metadata
            }
            for doc in documents
        ],
        "total": len(documents)
    }

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Download a document"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        file_content = download_file(document.file_path)
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=document.mime_type,
            headers={"Content-Disposition": f"attachment; filename={document.file_name}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Delete a document (soft delete)"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete from MinIO
        delete_file(document.file_path)
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{document_id}/versions")
def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get all versions of a document"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    versions = db.query(Document).filter(
        Document.entity_id == document.entity_id,
        Document.document_type == document.document_type
    ).order_by(Document.version.desc()).all()
    
    return {
        "document_id": document_id,
        "entity_id": document.entity_id,
        "document_type": document.document_type,
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "upload_time": v.upload_time,
                "uploaded_by": v.uploaded_by,
                "file_name": v.file_name,
                "file_size": v.file_size,
                "is_latest": v.is_latest == "true"
            }
            for v in versions
        ]
    }

@router.get("/supported-types")
def get_supported_document_types(
    user_id: int = Depends(get_current_user_id)
):
    """Get list of required and supported document types"""
    return {
        "required_documents": REQUIRED_DOCUMENTS,
        "supported_mime_types": list(SUPPORTED_MIME_TYPES),
        "supported_formats": ["PDF", "Excel (.xls, .xlsx)", "CSV", "Images (JPEG, PNG, GIF, WebP)"]
    }
