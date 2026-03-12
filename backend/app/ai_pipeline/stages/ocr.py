from typing import List, Tuple, Dict
import numpy as np

try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None

class OCRExtractor:
    """Stage 3: OCR extraction using PaddleOCR"""
    
    def __init__(self):
        """Initialize PaddleOCR model"""
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en') if PaddleOCR else None
    
    def run_ocr(self, image_path: str) -> Dict:
        """
        Extract text from document using PaddleOCR
        
        Returns:
        {
            "text": full_text,
            "blocks": [
                {
                    "text": block_text,
                    "bbox": [x1, y1, x2, y2],
                    "confidence": score
                }
            ],
            "raw_output": raw_paddleocr_output
        }
        """
        if self.ocr is None:
            return {
                "text": "",
                "blocks": [],
                "total_blocks": 0,
                "average_confidence": 0,
                "warning": "PaddleOCR dependency is not installed; OCR stage skipped."
            }

        result = self.ocr.ocr(image_path, cls=True)
        
        full_text = ""
        blocks = []
        
        for line in result:
            for word_info in line:
                # Extract text and bounding box
                text = word_info[1][0]
                confidence = word_info[1][1]
                bbox = word_info[0]
                
                # Convert bbox format: list of tuples to [x1, y1, x2, y2]
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                bbox_normalized = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                
                full_text += text + " "
                
                blocks.append({
                    "text": text,
                    "bbox": bbox_normalized,
                    "confidence": float(confidence)
                })
        
        return {
            "text": full_text.strip(),
            "blocks": blocks,
            "total_blocks": len(blocks),
            "average_confidence": np.mean([b["confidence"] for b in blocks]) if blocks else 0
        }
    
    def extract_text_with_positions(self, image_path: str) -> List[Dict]:
        """Extract text with precise positioning"""
        if self.ocr is None:
            return []

        result = self.ocr.ocr(image_path, cls=True)
        
        text_items = []
        for line in result:
            for word_info in line:
                text_items.append({
                    "text": word_info[1][0],
                    "confidence": float(word_info[1][1]),
                    "bbox": word_info[0]
                })
        
        return text_items
