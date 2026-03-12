"""Pydantic schemas for the extraction review API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Field-level detail (returned inside GET response)
# ---------------------------------------------------------------------------

class ExtractedField(BaseModel):
    value: Optional[Any] = None
    label: str
    unit: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: Optional[str] = None  # e.g. "balance_sheet_page_4"


# ---------------------------------------------------------------------------
# GET /extraction/results/{entity_id}
# ---------------------------------------------------------------------------

class ExtractionSection(BaseModel):
    """A named group of extracted fields (e.g. 'balance_sheet')."""
    section_key: str
    section_label: str
    fields: Dict[str, ExtractedField]
    average_confidence: float = 0.0


class ExtractionResultResponse(BaseModel):
    entity_id: int
    entity_name: Optional[str] = None
    result_id: Optional[int] = None
    document_id: Optional[int] = None
    status: str  # pending | approved | rejected

    sections: list[ExtractionSection]

    # If already reviewed, surface the corrections
    corrected_fields: Optional[Dict[str, Dict[str, Any]]] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    overall_confidence: float = 0.0
    total_fields: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /extraction/approve
# ---------------------------------------------------------------------------

class ApproveExtractionRequest(BaseModel):
    entity_id: int
    result_id: Optional[int] = None  # if None, approves the latest pending result

    # Nested dict: section_key -> { field_key -> corrected_value }
    corrected_fields: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    review_notes: Optional[str] = None
    status: str = Field(default="approved", pattern="^(approved|rejected)$")


class ApproveExtractionResponse(BaseModel):
    success: bool
    result_id: int
    entity_id: int
    status: str
    fields_corrected: int
    reviewed_at: datetime
    message: str
