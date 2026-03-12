from typing import Dict, Any, List, Tuple
import json
import os

try:
    from langchain.llms import OpenAI
except ImportError:
    OpenAI = None

class LLMValidator:
    """Stage 6: LLM validation using LangChain"""
    
    def __init__(self, api_key: str = None):
        """Initialize LLM (OpenAI or similar)"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # For now, we'll use a mock validator
        # In production, integrate with actual LLM
        self.llm = None
        if self.api_key and OpenAI is not None:
            try:
                self.llm = OpenAI(openai_api_key=self.api_key, temperature=0)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI: {e}")
    
    def validate_with_llm(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted financial data using LLM
        
        Returns:
        {
            "validation_passed": bool,
            "validations": [
                {
                    "field": str,
                    "value": Any,
                    "validation_status": "valid" | "invalid" | "uncertain",
                    "confidence": float,
                    "reason": str
                }
            ],
            "corrections": {
                "suggested": List[Dict],
                "applied": List[Dict]
            },
            "summary": str
        }
        """
        validations = []
        
        # Validate company info
        company_info = extracted_data.get("company_info", {})
        for field, value in company_info.items():
            if value:
                validation = self._validate_field(field, value)
                validations.append(validation)
        
        # Validate financial figures
        income_data = extracted_data.get("income_statement", {})
        for field, value in income_data.items():
            if value:
                validation = self._validate_financial_field(field, value)
                validations.append(validation)
        
        bs_data = extracted_data.get("balance_sheet", {})
        for field, value in bs_data.items():
            if value:
                validation = self._validate_financial_field(field, value)
                validations.append(validation)
        
        # Summary
        valid_count = sum(1 for v in validations if v["validation_status"] == "valid")
        invalid_count = sum(1 for v in validations if v["validation_status"] == "invalid")
        total_count = len(validations)

        if total_count == 0:
            passed = True
            confidence = 0.55
            summary = "Validation: no explicit fields validated; relying on extraction confidence"
        else:
            passed = invalid_count == 0 or (valid_count >= (total_count * 0.7))
            confidence = valid_count / total_count
            summary = f"Validation: {valid_count}/{total_count} fields valid ({(valid_count/total_count*100):.1f}%)"
        
        return {
            "validation_passed": passed,
            "validations": validations,
            "corrections": {
                "suggested": [],
                "applied": []
            },
            "summary": summary,
            "confidence": confidence
        }
    
    @staticmethod
    def _validate_field(field: str, value: Any) -> Dict[str, Any]:
        """Validate a single field"""
        # CIN validation: 21 characters
        if field == "cin":
            is_valid = isinstance(value, str) and len(value) == 21
            return {
                "field": field,
                "value": value,
                "validation_status": "valid" if is_valid else "invalid",
                "confidence": 0.95 if is_valid else 0.1,
                "reason": "CIN format matches (21 characters)" if is_valid else "CIN format invalid"
            }
        
        # PAN validation: 10 characters
        elif field == "pan":
            is_valid = isinstance(value, str) and len(value) == 10
            return {
                "field": field,
                "value": value,
                "validation_status": "valid" if is_valid else "invalid",
                "confidence": 0.95 if is_valid else 0.1,
                "reason": "PAN format matches (10 characters)" if is_valid else "PAN format invalid"
            }
        
        # Company name validation
        elif field == "company_name":
            is_valid = isinstance(value, str) and len(value) > 3
            return {
                "field": field,
                "value": value,
                "validation_status": "valid" if is_valid else "uncertain",
                "confidence": 0.85,
                "reason": "Company name extracted and reasonable length"
            }
        
        return {
            "field": field,
            "value": value,
            "validation_status": "valid",
            "confidence": 0.8,
            "reason": "Field validated"
        }
    
    @staticmethod
    def _validate_financial_field(field: str, value: float) -> Dict[str, Any]:
        """Validate financial field"""
        # Basic validation: positive values for most fields
        is_valid = isinstance(value, (int, float)) and value > 0
        
        status = "valid" if is_valid else "invalid"
        if field in ["equity", "net_income"] and isinstance(value, (int, float)):
            status = "valid"  # Can be negative
        
        polarity = "positive" if value > 0 else "negative"
        reason = f"Value {value} is {polarity}"
        
        return {
            "field": field,
            "value": value,
            "validation_status": status,
            "confidence": 0.9 if is_valid else 0.5,
            "reason": reason
        }
