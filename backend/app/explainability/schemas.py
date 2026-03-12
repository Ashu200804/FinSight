"""
Pydantic schemas for explainability API endpoints.

Validates input and output for explanation generation and retrieval.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# Enums
class DirectionEnum(str, Enum):
    """Direction of feature contribution"""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class ImpactLevelEnum(str, Enum):
    """Impact level of a feature"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SeverityEnum(str, Enum):
    """Severity level of risk"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CreditRatingEnum(str, Enum):
    """Credit rating"""
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    D = "D"


class CreditDecisionEnum(str, Enum):
    """Credit decision"""
    APPROVE = "APPROVE"
    CONDITIONAL_APPROVE = "CONDITIONAL_APPROVE"
    DECLINE = "DECLINE"


# Feature Importance Schema
class FeatureImportanceResponse(BaseModel):
    """Feature importance response"""
    feature_name: str
    importance_score: float = Field(..., ge=0, le=100)
    contribution: float
    direction: DirectionEnum
    impact_level: ImpactLevelEnum
    
    class Config:
        schema_extra = {
            "example": {
                "feature_name": "debt_to_equity",
                "importance_score": 85.5,
                "contribution": 0.245,
                "direction": "NEGATIVE",
                "impact_level": "CRITICAL"
            }
        }


# Risk Factor Schema
class RiskFactorResponse(BaseModel):
    """Risk factor response"""
    factor_name: str
    severity: SeverityEnum
    category: Optional[str] = None
    description: str
    recommendation: str
    supporting_metrics: Optional[Dict[str, float]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "factor_name": "High Financial Leverage",
                "severity": "HIGH",
                "category": "LEVERAGE",
                "description": "High leverage ratio indicates substantial financial risk",
                "recommendation": "Consider debt reduction strategy",
                "supporting_metrics": {"debt_to_equity": 2.5}
            }
        }


# Explanation Request/Response
class ExplanationRequest(BaseModel):
    """Request for credit decision explanation"""
    entity_id: int
    credit_decision_id: Optional[int] = None
    credit_score: float = Field(..., ge=0, le=1000)
    credit_rating: CreditRatingEnum
    decision: CreditDecisionEnum
    
    # Input features
    features: Dict[str, float]
    feature_names: List[str]
    
    # Financial metrics
    metrics: Dict[str, float]
    
    # Optional research findings
    research_findings: Optional[Dict[str, Any]] = None
    
    # Model information
    model_version: str = "1.0"
    model_type: str = "xgboost"
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": 123,
                "credit_score": 750,
                "credit_rating": "A",
                "decision": "APPROVE",
                "features": {
                    "debt_to_equity": 1.2,
                    "current_ratio": 1.8,
                    "debt_service_coverage_ratio": 2.1
                },
                "feature_names": ["debt_to_equity", "current_ratio", "debt_service_coverage_ratio"],
                "metrics": {
                    "debt_to_equity": 1.2,
                    "current_ratio": 1.8,
                    "debt_service_coverage_ratio": 2.1,
                    "net_profit_margin": 0.12,
                    "return_on_assets": 0.09
                }
            }
        }


class ExplanationResponse(BaseModel):
    """Complete credit decision explanation response"""
    decision_id: str
    applicant_name: Optional[str] = None
    final_score: float = Field(..., ge=0, le=1000)
    final_rating: CreditRatingEnum
    decision: CreditDecisionEnum
    decision_confidence: float = Field(..., ge=0, le=1)
    
    # SHAP Analysis
    feature_importance: List[FeatureImportanceResponse]
    top_contributing_factors: List[str]
    top_risk_factors: List[RiskFactorResponse]
    
    # Human-Readable Explanations
    executive_summary: str
    key_findings: List[str]
    strengths: List[str]
    concerns: List[str]
    recommendations: List[str]
    
    # Sensitivity Analysis
    sensitivity_analysis: Dict[str, Dict[str, float]]
    
    # Metadata
    generated_at: str
    explanation_confidence: float = Field(..., ge=0, le=1)
    
    class Config:
        schema_extra = {
            "example": {
                "decision_id": "DEC-2024-001",
                "applicant_name": "Acme Corporation",
                "final_score": 750,
                "final_rating": "A",
                "decision": "APPROVE",
                "decision_confidence": 0.92,
                "feature_importance": [{
                    "feature_name": "debt_to_equity",
                    "importance_score": 85.5,
                    "contribution": 0.245,
                    "direction": "NEGATIVE",
                    "impact_level": "CRITICAL"
                }],
                "top_contributing_factors": [
                    "debt_to_equity (decreasing probability by 24.5%)",
                    "current_ratio (increasing probability by 18.3%)"
                ],
                "top_risk_factors": [{
                    "factor_name": "High Financial Leverage",
                    "severity": "HIGH",
                    "description": "Debt-to-equity ratio of 1.8 indicates elevated leverage",
                    "recommendation": "Monitor quarterly debt levels"
                }],
                "executive_summary": "Acme Corporation is recommended for approval with A rating.",
                "key_findings": [
                    "Factor 1: debt_to_equity is critical (negative impact on creditworthiness)",
                    "Factor 2: current_ratio is high (positive impact on creditworthiness)"
                ],
                "strengths": [
                    "Conservative capital structure with low leverage",
                    "Strong profitability and margin control"
                ],
                "concerns": [
                    "High Financial Leverage - Debt-to-equity ratio indicates substantial financial risk"
                ],
                "recommendations": [
                    "Standard approval process recommended",
                    "Monitor quarterly debt levels"
                ],
                "sensitivity_analysis": {
                    "debt_to_equity": {
                        "base_value": 1.2,
                        "impact_at_minus_30pc": 0.84,
                        "impact_at_plus_30pc": 1.56
                    }
                },
                "generated_at": "2024-01-20T14:30:00Z",
                "explanation_confidence": 0.92
            }
        }


# Simplified explanation response (for list views)
class ExplanationSummaryResponse(BaseModel):
    """Summary explanation for list views"""
    decision_id: str
    entity_id: int
    credit_rating: CreditRatingEnum
    decision: CreditDecisionEnum
    decision_confidence: float
    top_contributing_factors: List[str]
    generated_at: str
    explanation_confidence: float


# Batch explanation request
class BatchExplanationRequest(BaseModel):
    """Request for batch explanations"""
    entity_ids: List[int] = Field(..., max_items=100)
    include_sensitivity: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "entity_ids": [123, 124, 125],
                "include_sensitivity": True
            }
        }


class BatchExplanationResponse(BaseModel):
    """Batch explanation response"""
    total_explanations: int
    explanations: List[ExplanationSummaryResponse]
    generated_at: str


# Sensitivity Analysis Schema
class SensitivityAnalysisRequest(BaseModel):
    """Request for sensitivity analysis on a decision"""
    decision_id: str
    metric_name: str
    variation_percentages: List[float] = Field(default=[-30, -20, -10, 10, 20, 30])
    
    class Config:
        schema_extra = {
            "example": {
                "decision_id": "DEC-2024-001",
                "metric_name": "debt_to_equity",
                "variation_percentages": [-30, -20, -10, 10, 20, 30]
            }
        }


class SensitivityAnalysisResponse(BaseModel):
    """Sensitivity analysis response"""
    decision_id: str
    metric_name: str
    base_value: float
    base_score: float
    analysis: Dict[str, float]  # % change -> new score
    elasticity: float  # Score change per metric unit
    
    class Config:
        schema_extra = {
            "example": {
                "decision_id": "DEC-2024-001",
                "metric_name": "debt_to_equity",
                "base_value": 1.5,
                "base_score": 750,
                "analysis": {
                    "-30": 820,
                    "-20": 805,
                    "-10": 778,
                    "10": 722,
                    "20": 695,
                    "30": 668
                },
                "elasticity": 0.85
            }
        }


# Feature Comparison Schema
class FeatureComparisonRequest(BaseModel):
    """Request to compare feature importance across multiple decisions"""
    decision_ids: List[str] = Field(..., max_items=10)
    top_n_features: int = Field(default=10, ge=1, le=50)
    
    class Config:
        schema_extra = {
            "example": {
                "decision_ids": ["DEC-2024-001", "DEC-2024-002"],
                "top_n_features": 10
            }
        }


class FeatureComparison(BaseModel):
    """Feature comparison for a single feature across decisions"""
    feature_name: str
    comparisons: Dict[str, float]  # decision_id -> importance_score


class FeatureComparisonResponse(BaseModel):
    """Feature comparison response"""
    feature_comparisons: List[FeatureComparison]
    total_decisions: int


# Explanation Review Schema
class ExplanationReviewRequest(BaseModel):
    """Request to review/approve an explanation"""
    explanation_id: int
    action: str = Field(..., pattern="^(APPROVE|REJECT|REQUEST_REVISION)$")
    notes: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "explanation_id": 1,
                "action": "APPROVE",
                "notes": "Explanation is clear and well-supported"
            }
        }


class ExplanationReviewResponse(BaseModel):
    """Review response"""
    explanation_id: int
    action: str
    reviewed_by: str
    reviewed_at: str
    message: str


# Risk Factor Analysis Schema
class RiskFactorAnalysisRequest(BaseModel):
    """Request for risk factor analysis"""
    entity_id: int
    include_mitigants: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": 123,
                "include_mitigants": True
            }
        }


class RiskFactorAnalysisResponse(BaseModel):
    """Risk factor analysis response"""
    entity_id: int
    total_risk_factors: int
    critical_risks: List[RiskFactorResponse]
    high_risks: List[RiskFactorResponse]
    medium_risks: List[RiskFactorResponse]
    aggregate_risk_score: float = Field(..., ge=0, le=100)
    risk_trend: str  # IMPROVING, STABLE, DETERIORATING
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": 123,
                "total_risk_factors": 4,
                "critical_risks": [],
                "high_risks": [{
                    "factor_name": "High Financial Leverage",
                    "severity": "HIGH",
                    "description": "Debt-to-equity ratio is elevated",
                    "recommendation": "Monitor quarterly"
                }],
                "medium_risks": [],
                "aggregate_risk_score": 65.5,
                "risk_trend": "STABLE"
            }
        }


# Comparison Report Schema
class ComparisonReportRequest(BaseModel):
    """Request for comparison of entities"""
    entity_ids: List[int] = Field(..., min_items=2, max_items=5)
    comparison_metrics: List[str] = Field(
        default=["credit_score", "risk_factors", "feature_importance"]
    )
    
    class Config:
        schema_extra = {
            "example": {
                "entity_ids": [123, 124],
                "comparison_metrics": ["credit_score", "risk_factors"]
            }
        }


class EntityComparison(BaseModel):
    """Comparison data for a single entity"""
    entity_id: int
    entity_name: str
    credit_score: float
    credit_rating: CreditRatingEnum
    risk_score: float
    top_3_factors: List[str]


class ComparisonReportResponse(BaseModel):
    """Comparison report response"""
    comparison_type: str  # PEER, PORTFOLIO, CUSTOM
    entities: List[EntityComparison]
    generated_at: str
    insights: List[str]


class SWOTAnalysisRequest(BaseModel):
    """Request payload for LLM-generated SWOT analysis"""
    entity_id: Optional[int] = None
    company_name: str = Field(..., min_length=2, max_length=255)
    financial_metrics: Dict[str, float]
    market_sentiment: Dict[str, Any]
    industry_data: Dict[str, Any]
    model: str = Field(default="gpt-4o-mini")

    class Config:
        schema_extra = {
            "example": {
                "entity_id": 123,
                "company_name": "Acme Manufacturing Pvt Ltd",
                "financial_metrics": {
                    "debt_to_equity": 1.2,
                    "current_ratio": 1.8,
                    "debt_service_coverage_ratio": 1.9,
                    "net_profit_margin": 0.11,
                    "return_on_assets": 0.08
                },
                "market_sentiment": {
                    "composite_sentiment_score": 0.42,
                    "market_tone": "POSITIVE",
                    "analyst_rating": "BUY",
                    "negative_mentions": 35
                },
                "industry_data": {
                    "industry": "Manufacturing",
                    "growth_rate_cagr": 9.5,
                    "market_attractiveness": "ATTRACTIVE",
                    "regulatory_environment": "NEUTRAL"
                },
                "model": "gpt-4o-mini"
            }
        }


class SWOTAnalysisResponse(BaseModel):
    """LLM-generated SWOT output"""
    company_name: str
    strengths: List[str]
    weaknesses: List[str]
    opportunities: List[str]
    threats: List[str]
    generated_at: str
    model_used: str

    class Config:
        schema_extra = {
            "example": {
                "company_name": "Acme Manufacturing Pvt Ltd",
                "strengths": [
                    "Healthy liquidity (current ratio 1.8x) supports near-term obligations",
                    "Positive market tone with favorable analyst stance"
                ],
                "weaknesses": [
                    "Leverage remains above conservative levels for the sector"
                ],
                "opportunities": [
                    "Industry CAGR near double digits supports revenue expansion"
                ],
                "threats": [
                    "Potential margin pressure from input cost volatility"
                ],
                "generated_at": "2026-03-11T10:30:00",
                "model_used": "gpt-4o-mini"
            }
        }


# Error Schema
class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    details: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: str
