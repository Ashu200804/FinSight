from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.storage.minio_client import download_file
from app.ai_pipeline.pipeline import DocumentExtractionPipeline
from app.extraction.models import ExtractionResult
from app.ai_pipeline.stages.schema_mapper import FinancialSchemaMapper
from app.ai_pipeline.stages.ai_structurer import AIStructurer
from app.ai_pipeline.stages.llm_validator import LLMValidator
from app.ai_pipeline.stages.consistency_checker import FinancialConsistencyChecker
from app.utils.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import tempfile
import os
from typing import Optional, Dict

try:
    import pandas as pd
except Exception:
    pd = None

router = APIRouter(prefix="/ai/extract", tags=["ai-extraction"])
security = HTTPBearer()

def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> int:
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return int(payload.get("sub"))

def get_document_extraction_results(document_id: int, db: Session) -> Optional[Dict]:
    """
    Helper function to retrieve extraction results for a document.
    This function is used by the metrics engine to get processed data.
    
    For now, as processing results are not persisted, this function
    would need to be enhanced to query a processing results table.
    
    Args:
        document_id: ID of the document
        db: Database session
        
    Returns:
        Dictionary with extraction results or None
    """
    result = (
        db.query(ExtractionResult)
        .filter(ExtractionResult.document_id == document_id)
        .order_by(ExtractionResult.id.desc())
        .first()
    )

    if not result:
        return None

    extracted_payload = result.extracted_fields or {}
    if isinstance(extracted_payload, dict) and extracted_payload.get('extracted_data'):
        extracted_payload = extracted_payload.get('extracted_data')

    corrected = result.corrected_fields or {}
    if corrected and isinstance(extracted_payload, dict):
        merged = dict(extracted_payload)
        for section_key, section_updates in corrected.items():
            section_values = dict(merged.get(section_key, {})) if isinstance(merged.get(section_key, {}), dict) else {}
            if isinstance(section_updates, dict):
                section_values.update(section_updates)
            merged[section_key] = section_values
        extracted_payload = merged

    return {
        'extracted_data': extracted_payload if isinstance(extracted_payload, dict) else {},
        'result_id': result.id,
        'status': result.status,
    }


def _persist_extraction_result(db: Session, entity_id: int, document_id: int, results: Dict) -> None:
    extracted_data = results.get('extracted_data') if isinstance(results, dict) else {}
    if not isinstance(extracted_data, dict):
        extracted_data = {}

    db.query(ExtractionResult).filter(ExtractionResult.document_id == document_id).delete()

    db_record = ExtractionResult(
        entity_id=entity_id,
        document_id=document_id,
        extracted_fields=extracted_data,
        status='pending',
    )
    db.add(db_record)
    db.commit()


def _process_tabular_document(file_path: str) -> Dict:
    if pd is None:
        raise Exception("Pandas is required for CSV/Excel processing but is not installed")

    file_lower = file_path.lower()
    if file_lower.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_lower.endswith('.xlsx') or file_lower.endswith('.xls'):
        df = pd.read_excel(file_path)
    else:
        raise Exception("Unsupported tabular format")

    if df.empty:
        raise Exception("Uploaded tabular file is empty")

    headers = [str(col).strip() for col in df.columns]
    row_data = df.fillna("").astype(str).values.tolist()
    ocr_text = "\n".join([" | ".join(headers)] + [" | ".join(str(cell) for cell in row) for row in row_data])

    mapped_input = {
        "ocr_text": ocr_text,
        "tables": [
            {
                "table_num": 1,
                "rows": len(row_data),
                "cols": len(headers),
                "headers": headers,
                "data": row_data,
                "confidence": 0.99,
            }
        ],
    }

    extracted_data = FinancialSchemaMapper.map_schema(mapped_input)
    ai_result = AIStructurer().structure_financial_data(mapped_input, extracted_data)
    extracted_data = ai_result.get("structured_data", extracted_data)
    validation_results = LLMValidator().validate_with_llm(extracted_data)
    consistency_results = FinancialConsistencyChecker.run_consistency_checks(extracted_data)

    extracted_count = len(extracted_data.get("extracted_fields", []))
    coverage_score = min(1.0, extracted_count / 18.0)
    overall_confidence = round(
        (coverage_score * 0.35) +
        (validation_results.get("confidence", 0) * 0.25) +
        ((1.0 if consistency_results.get("passed") else 0.6) * 0.2) +
        (ai_result.get("confidence", 0) * 0.2),
        3
    )

    return {
        "status": "success",
        "pipeline_stages": {
            "preprocessing": {"status": "completed", "preprocessing_applied": False},
            "layout_detection": {"status": "completed", "layout_info": {"layout_type": "tabular"}},
            "ocr_extraction": {"status": "completed", "total_blocks": 0, "average_confidence": 1.0},
            "table_extraction": {"status": "completed", "tables_found": 1},
            "schema_mapping": {"status": "completed", "mapped_fields": list(extracted_data.keys())},
            "ai_structuring": {
                "status": "completed" if ai_result.get("used_ai") else "skipped",
                "used_ai": ai_result.get("used_ai", False),
                "confidence": ai_result.get("confidence", 0),
                "warnings": ai_result.get("warnings", []),
            },
            "llm_validation": {"status": "completed", "validation_passed": validation_results.get("validation_passed", False), "confidence": validation_results.get("confidence", 0)},
            "consistency_checks": {"status": "completed", "all_checks_passed": consistency_results.get("passed", False), "summary": consistency_results.get("summary", {}).get("passed", 0)},
        },
        "extracted_data": extracted_data,
        "validation_results": validation_results,
        "consistency_results": consistency_results,
        "overall_confidence": overall_confidence,
        "warnings": ai_result.get("warnings", []),
    }


@router.post("/process-document")
async def process_document(
    file: UploadFile = File(...),
    entity_id: int = Form(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Process financial document through AI extraction pipeline
    
    Returns structured financial JSON with validation and consistency checks
    """
    
    if not entity_id or not document_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="entity_id and document_type are required"
        )
    
    try:
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        
        # Write file
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        if file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            results = _process_tabular_document(temp_path)
        else:
            pipeline = DocumentExtractionPipeline()
            results = pipeline.process_document(temp_path)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "status": "success",
            "processing_results": results,
            "entity_id": entity_id,
            "document_type": document_type,
            "uploaded_by": user_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )

@router.get("/process-document/{document_id}")
async def process_stored_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Process a document already stored in the vault
    
    Args:
        document_id: ID of document in vault
    
    Returns:
        Extraction results
    """
    
    try:
        from app.models.document import Document
        
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Download file from MinIO
        file_content = download_file(document.file_path)
        
        # Save to temp location
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, document.file_name)
        
        with open(temp_path, "wb") as f:
            f.write(file_content)

        if (document.file_name or "").lower().endswith(('.csv', '.xlsx', '.xls')):
            results = _process_tabular_document(temp_path)
        else:
            pipeline = DocumentExtractionPipeline()
            results = pipeline.process_document(temp_path)

        if results.get("status") == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=results.get("message") or results.get("error") or "Document processing failed"
            )
        
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        _persist_extraction_result(db=db, entity_id=document.entity_id, document_id=document.id, results=results)

        return {
            "status": "success",
            "document_id": document_id,
            "document_name": document.file_name,
            "document_type": document.document_type,
            "processing_results": results
        }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )

@router.post("/batch-process")
async def batch_process_documents(
    entity_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Process all documents for an entity
    
    Returns consolidated extraction results
    """
    
    try:
        from app.models.document import Document
        
        # Get all documents for entity
        documents = db.query(Document).filter(
            Document.entity_id == entity_id,
            Document.is_latest == "true"
        ).all()
        
        if not documents:
            return {
                "status": "success",
                "message": "No documents found for entity",
                "entity_id": entity_id,
                "documents_processed": 0,
                "results": []
            }
        
        results = []
        
        for doc in documents:
            try:
                # Download and process each document
                file_content = download_file(doc.file_path)
                
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, doc.file_name)
                
                with open(temp_path, "wb") as f:
                    f.write(file_content)
                
                pipeline = DocumentExtractionPipeline()
                processing_result = pipeline.process_document(temp_path)

                if processing_result.get("status") != "error":
                    _persist_extraction_result(db=db, entity_id=doc.entity_id, document_id=doc.id, results=processing_result)
                
                results.append({
                    "document_id": doc.id,
                    "document_name": doc.file_name,
                    "document_type": doc.document_type,
                    "results": processing_result
                })
                
                # Clean up
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            except Exception as e:
                results.append({
                    "document_id": doc.id,
                    "document_name": doc.file_name,
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "entity_id": entity_id,
            "documents_processed": len(results),
            "results": results
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Batch processing failed"
        }

@router.get("/pipeline-info")
async def get_pipeline_info(
    user_id: int = Depends(get_current_user_id)
):
    """Get information about the extraction pipeline"""
    
    return {
        "pipeline_name": "DocumentExtractionPipeline",
        "version": "1.0.0",
        "stages": [
            "Document preprocessing",
            "Layout detection",
            "OCR extraction",
            "Table extraction",
            "Schema mapping",
            "AI structuring",
            "LLM validation",
            "Financial consistency checks"
        ],
        "supported_formats": [
            "PDF",
            "PNG",
            "JPEG",
            "TIFF"
        ],
        "output_format": "JSON",
        "capabilities": {
            "ocr": "PaddleOCR",
            "table_extraction": "Camelot",
            "preprocessing": "OpenCV",
            "validation": "LLM + Rule-based",
            "consistency_checks": "Financial accounting rules"
        }
    }
