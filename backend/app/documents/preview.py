from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.models.document import Document
from app.database.config import get_db
from app.storage.minio_client import download_file
from app.utils.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import base64

router = APIRouter(prefix="/documents/preview", tags=["preview"])
security = HTTPBearer()

def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> int:
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return int(payload.get("sub"))

@router.get("/{document_id}")
def get_document_preview(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Get document preview (for PDF, images, etc.)"""
    
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        file_content = download_file(document.file_path)
        
        # Return base64 encoded preview for images and PDFs
        if document.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            encoded = base64.b64encode(file_content).decode('utf-8')
            return {
                "id": document.id,
                "file_name": document.file_name,
                "mime_type": document.mime_type,
                "file_size": document.file_size,
                "preview_data": f"data:{document.mime_type};base64,{encoded}",
                "preview_type": "image" if document.mime_type.startswith("image") else "pdf"
            }
        
        # For Excel and CSV, return metadata only
        elif document.mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv']:
            return {
                "id": document.id,
                "file_name": document.file_name,
                "mime_type": document.mime_type,
                "file_size": document.file_size,
                "preview_type": "spreadsheet",
                "message": "Download file to view contents"
            }
        
        else:
            return {
                "id": document.id,
                "file_name": document.file_name,
                "mime_type": document.mime_type,
                "file_size": document.file_size,
                "preview_type": "unknown",
                "message": "Preview not available for this file type"
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
