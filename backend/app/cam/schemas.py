"""Pydantic schemas for CAM history APIs."""

from datetime import datetime
from pydantic import BaseModel
from typing import Dict, List, Optional


class CAMReportHistoryItem(BaseModel):
    id: int
    entity_id: int
    credit_score: Optional[float] = None
    risk_category: Optional[str] = None
    approval_probability: Optional[float] = None
    created_at: datetime
    download_url: str


class CAMReportHistoryResponse(BaseModel):
    entity_id: int
    total_reports: int
    reports: List[CAMReportHistoryItem]


class CAMPreviewScorecard(BaseModel):
    credit_score: Optional[float] = None
    risk_category: Optional[str] = None
    probability_of_default: Optional[float] = None
    financial_grade: Optional[str] = None
    decision: Optional[str] = None


class CAMPreviewRecommendation(BaseModel):
    decision: str
    requested_amount: Optional[str] = None
    suggested_rate_guidance: Optional[str] = None
    key_conditions: Optional[str] = None
    rationale: Optional[str] = None


class CAMPreviewResponse(BaseModel):
    entity_id: int
    entity_name: str
    generated_at: datetime
    scorecard: CAMPreviewScorecard
    financial_analysis: Dict[str, float]
    market_snapshot: Dict[str, str | float]
    top_feature_importance: List[str]
    top_risk_factors: List[str]
    swot: Dict[str, List[str]]
    recommendation: CAMPreviewRecommendation
