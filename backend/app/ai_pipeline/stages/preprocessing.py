import cv2
import numpy as np
from typing import Tuple
import os

class DocumentPreprocessor:
    """Stage 1: Document preprocessing"""
    
    @staticmethod
    def preprocess_document(image_path: str) -> np.ndarray:
        """
        Preprocess document image for better OCR results
        
        Steps:
        1. Load image
        2. Convert to grayscale
        3. Denoise
        4. Apply thresholding
        5. Deskew (if needed)
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Apply thresholding
        _, binary = cv2.threshold(enhanced, 150, 255, cv2.THRESH_BINARY)
        
        # Deskew
        deskewed = DocumentPreprocessor._deskew(binary)
        
        return deskewed
    
    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        """Deskew document image"""
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(cv2.convexHull(coords))[2]
        
        if angle < -45:
            angle = 90 + angle
        
        if abs(angle) > 1:  # Only rotate if angle is significant
            h, w = image.shape
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                     borderMode=cv2.BORDER_REFLECT)
            return rotated
        
        return image
    
    @staticmethod
    def save_preprocessed(image: np.ndarray, output_path: str) -> None:
        """Save preprocessed image"""
        cv2.imwrite(output_path, image)
