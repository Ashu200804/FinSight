from pdf2image import convert_from_path
from typing import Dict, Any, List
import tempfile
import os

from .stages.preprocessing import DocumentPreprocessor
from .stages.ocr import OCRExtractor
from .stages.table_extraction import TableExtractor
from .stages.schema_mapper import FinancialSchemaMapper
from .stages.ai_structurer import AIStructurer
from .stages.llm_validator import LLMValidator
from .stages.consistency_checker import FinancialConsistencyChecker

class DocumentExtractionPipeline:
    """
    Production-grade Document AI pipeline for financial document processing
    
    Stages:
    1. Document preprocessing
    2. Layout detection
    3. OCR extraction
    4. Table extraction
    5. Schema mapping
    6. LLM validation
    7. Financial consistency checks
    """
    
    def __init__(self, openai_api_key: str = None):
        """Initialize pipeline components"""
        self.preprocessor = DocumentPreprocessor()
        self.ocr_extractor = OCRExtractor()
        self.table_extractor = TableExtractor()
        self.schema_mapper = FinancialSchemaMapper()
        self.ai_structurer = AIStructurer(api_key=openai_api_key)
        self.llm_validator = LLMValidator(api_key=openai_api_key)
        self.consistency_checker = FinancialConsistencyChecker()
        
        self.pipeline_results = {}
    
    def process_document(self, document_path: str) -> Dict[str, Any]:
        """
        Run full document extraction pipeline
        
        Args:
            document_path: Path to PDF or image document
        
        Returns:
            Structured financial JSON with all pipeline results
        """
        try:
            original_document_path = document_path
            pdf_processing_warning = None
            fallback_pdf_text = ""

            # Convert PDF to images if needed
            if document_path.lower().endswith('.pdf'):
                try:
                    images = self._pdf_to_images(document_path)
                    # Process first page for now
                    if images:
                        document_path = images[0]
                except Exception as conversion_error:
                    pdf_processing_warning = str(conversion_error)
                    fallback_pdf_text = self._extract_pdf_text_fallback(original_document_path)
            
            # Stage 1: Preprocessing + Stage 2/3 OCR path (only when we have an image path)
            preprocessed_image = None
            layout_info = {}
            ocr_results = {
                "text": fallback_pdf_text,
                "blocks": [],
                "total_blocks": 0,
                "average_confidence": 0,
            }

            can_run_image_pipeline = not original_document_path.lower().endswith('.pdf') or document_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))

            if can_run_image_pipeline:
                # Stage 1: Preprocessing
                preprocessed_image = self.preprocess_document(document_path)

                # Stage 2: Layout detection (implicit in preprocessing)
                layout_info = self._detect_layout(preprocessed_image)

                # Stage 3: OCR extraction
                ocr_results = self.run_ocr(preprocessed_image)
            elif original_document_path.lower().endswith('.pdf'):
                layout_info = {
                    "layout_type": "pdf_fallback",
                    "pages": 1,
                    "detected_sections": ["text_fallback", "table_extraction"]
                }
            
            # Stage 4: Table extraction (PDF only)
            table_results = {}
            if original_document_path.lower().endswith('.pdf'):
                table_results = self.extract_tables(original_document_path)
            
            # Combine OCR and table data
            combined_data = {
                "ocr_text": ocr_results.get("text"),
                "ocr_blocks": ocr_results.get("blocks"),
                "tables": table_results.get("tables", [])
            }
            
            # Stage 5: Schema mapping
            schema_mapped = self.map_schema(combined_data)

            # Stage 6: AI structuring (optional, guarded)
            ai_result = self.structure_with_ai(combined_data, schema_mapped)
            schema_mapped = ai_result.get("structured_data", schema_mapped)
            
            # Stage 7: LLM validation
            llm_results = self.validate_with_llm(schema_mapped)
            
            # Stage 8: Consistency checks
            consistency_results = self.run_consistency_checks(schema_mapped)
            
            # Compile final result
            final_result = {
                "status": "success",
                "document_path": document_path,
                "pipeline_stages": {
                    "preprocessing": {
                        "status": "completed" if preprocessed_image else "skipped",
                        "preprocessing_applied": bool(preprocessed_image)
                    },
                    "layout_detection": {
                        "status": "completed" if layout_info else "skipped",
                        "layout_info": layout_info
                    },
                    "ocr_extraction": {
                        "status": "completed" if can_run_image_pipeline else "fallback",
                        "total_blocks": ocr_results.get("total_blocks"),
                        "average_confidence": ocr_results.get("average_confidence")
                    },
                    "table_extraction": {
                        "status": "completed",
                        "tables_found": table_results.get("tables_found", 0)
                    },
                    "schema_mapping": {
                        "status": "completed",
                        "mapped_fields": list(schema_mapped.keys())
                    },
                    "ai_structuring": {
                        "status": "completed" if ai_result.get("used_ai") else "skipped",
                        "used_ai": ai_result.get("used_ai", False),
                        "confidence": ai_result.get("confidence", 0),
                        "warnings": ai_result.get("warnings", [])
                    },
                    "llm_validation": {
                        "status": "completed",
                        "validation_passed": llm_results["validation_passed"],
                        "confidence": llm_results.get("confidence", 0)
                    },
                    "consistency_checks": {
                        "status": "completed",
                        "all_checks_passed": consistency_results["passed"],
                        "summary": consistency_results["summary"]["passed"]
                    }
                },
                "extracted_data": schema_mapped,
                "validation_results": llm_results,
                "consistency_results": consistency_results,
                "overall_confidence": self._calculate_overall_confidence(
                    ocr_results, llm_results, consistency_results, ai_result
                ),
                "warnings": ai_result.get("warnings", [])
            }

            if pdf_processing_warning:
                existing_warnings = final_result.get("warnings", [])
                existing_warnings.append(f"PDF image conversion fallback used: {pdf_processing_warning}")
                final_result["warnings"] = existing_warnings
            
            self.pipeline_results = final_result
            return final_result
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Pipeline processing failed: {str(e)}"
            }

    @staticmethod
    def _extract_pdf_text_fallback(pdf_path: str) -> str:
        """Extract text from PDF without Poppler (best-effort fallback)."""
        readers = []

        try:
            from pypdf import PdfReader  # type: ignore
            readers.append(PdfReader)
        except Exception:
            pass

        try:
            from PyPDF2 import PdfReader as LegacyPdfReader  # type: ignore
            readers.append(LegacyPdfReader)
        except Exception:
            pass

        for reader_cls in readers:
            try:
                reader = reader_cls(pdf_path)
                pages_text = []
                for page in getattr(reader, 'pages', [])[:3]:
                    page_text = page.extract_text() or ""
                    if page_text:
                        pages_text.append(page_text)
                if pages_text:
                    return "\n".join(pages_text)
            except Exception:
                continue

        return ""
    
    def preprocess_document(self, image_path: str) -> str:
        """Stage 1: Preprocess document"""
        try:
            preprocessed = self.preprocessor.preprocess_document(image_path)
            
            # Save preprocessed image
            temp_dir = tempfile.gettempdir()
            preprocessed_path = os.path.join(temp_dir, "preprocessed_document.png")
            self.preprocessor.save_preprocessed(preprocessed, preprocessed_path)
            
            return preprocessed_path
        except Exception as e:
            raise Exception(f"Preprocessing failed: {str(e)}")
    
    def _detect_layout(self, image_path: str) -> Dict[str, Any]:
        """Stage 2: Detect document layout"""
        # Placeholder for layout detection
        # In production, integrate LayoutParser or similar
        return {
            "layout_type": "financial_statement",
            "pages": 1,
            "detected_sections": ["header", "financial_data", "footer"]
        }
    
    def run_ocr(self, image_path: str) -> Dict[str, Any]:
        """Stage 3: Run OCR extraction"""
        try:
            return self.ocr_extractor.run_ocr(image_path)
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def extract_tables(self, pdf_path: str) -> Dict[str, Any]:
        """Stage 4: Extract tables from PDF"""
        try:
            return self.table_extractor.extract_tables(pdf_path)
        except Exception as e:
            return {
                "tables_found": 0,
                "tables": [],
                "error": str(e)
            }
    
    def map_schema(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 5: Map to financial schema"""
        try:
            return self.schema_mapper.map_schema(extracted_data)
        except Exception as e:
            raise Exception(f"Schema mapping failed: {str(e)}")

    def structure_with_ai(self, extracted_data: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 6: Use LLM to structure/complete schema with strict guardrails"""
        try:
            return self.ai_structurer.structure_financial_data(extracted_data, baseline)
        except Exception as e:
            return {
                "structured_data": baseline,
                "used_ai": False,
                "confidence": 0.0,
                "warnings": [str(e)],
            }
    
    def validate_with_llm(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 7: Validate with LLM"""
        try:
            return self.llm_validator.validate_with_llm(extracted_data)
        except Exception as e:
            return {
                "validation_passed": False,
                "validations": [],
                "error": str(e)
            }
    
    def run_consistency_checks(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 8: Run financial consistency checks"""
        try:
            return self.consistency_checker.run_consistency_checks(financial_data)
        except Exception as e:
            return {
                "passed": False,
                "checks": [],
                "error": str(e)
            }
    
    @staticmethod
    def _pdf_to_images(pdf_path: str, first_page_only: bool = True) -> List[str]:
        """Convert PDF to images"""
        try:
            pages = 1 if first_page_only else 0
            images = convert_from_path(pdf_path, first_page=pages)
            
            temp_dir = tempfile.gettempdir()
            image_paths = []
            
            for idx, image in enumerate(images):
                image_path = os.path.join(temp_dir, f"page_{idx + 1}.png")
                image.save(image_path, "PNG")
                image_paths.append(image_path)
            
            return image_paths
        except Exception as e:
            raise Exception(f"PDF to image conversion failed: {str(e)}")
    
    @staticmethod
    def _calculate_overall_confidence(ocr_results: Dict, llm_results: Dict,
                                     consistency_results: Dict, ai_result: Dict = None) -> float:
        """Calculate overall pipeline confidence"""
        ocr_confidence = ocr_results.get("average_confidence", 0)
        llm_confidence = llm_results.get("confidence", 0)
        consistency_score = 1.0 if consistency_results.get("passed") else 0.5
        ai_confidence = (ai_result or {}).get("confidence", 0)
        
        # Weighted average
        overall = (
            (ocr_confidence * 0.30) +
            (llm_confidence * 0.30) +
            (consistency_score * 0.20) +
            (ai_confidence * 0.20)
        )
        return round(overall, 3)
    
    def get_pipeline_results(self) -> Dict[str, Any]:
        """Get last pipeline results"""
        return self.pipeline_results
