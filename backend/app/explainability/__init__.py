"""
Explainability Module - SHAP-based Credit Decision Explanations

Provides comprehensive explanations for credit underwriting decisions
using SHapley Additive exPlanations (SHAP) values.

Exports:
    - SHAPExplainer: Core SHAP value calculation engine
    - CreditDecisionExplainer: Credit-specific explanation generator
    - CreditDecisionExplanation: Data class for complete explanations
    - Models: Database models for storing explanations
    - Schemas: Pydantic validation schemas
    - Routes: FastAPI endpoints for explanation API
"""

from app.explainability.explainability_engine import (
    SHAPExplainer,
    CreditDecisionExplainer,
    CreditDecisionExplanation,
    FeatureImportance,
    RiskFactor,
    SWOTLLMGenerator,
    create_mock_explainer,
)
from app.explainability.models import (
    ExplanationModel,
    FeatureImportanceModel,
    RiskFactorModel,
    ExplanationAuditLog,
    FeatureImportanceCache,
    ExplanationTemplate,
)
from app.explainability.schemas import (
    ExplanationRequest,
    ExplanationResponse,
    ExplanationSummaryResponse,
    BatchExplanationRequest,
    BatchExplanationResponse,
    SensitivityAnalysisRequest,
    SensitivityAnalysisResponse,
    FeatureComparisonRequest,
    FeatureComparisonResponse,
    RiskFactorAnalysisRequest,
    RiskFactorAnalysisResponse,
    ComparisonReportRequest,
    ComparisonReportResponse,
    SWOTAnalysisRequest,
    SWOTAnalysisResponse,
)
from app.explainability.routes import router

__all__ = [
    # Engine
    'SHAPExplainer',
    'CreditDecisionExplainer',
    'CreditDecisionExplanation',
    'FeatureImportance',
    'RiskFactor',
    'SWOTLLMGenerator',
    'create_mock_explainer',
    # Models
    'ExplanationModel',
    'FeatureImportanceModel',
    'RiskFactorModel',
    'ExplanationAuditLog',
    'FeatureImportanceCache',
    'ExplanationTemplate',
    # Schemas
    'ExplanationRequest',
    'ExplanationResponse',
    'ExplanationSummaryResponse',
    'BatchExplanationRequest',
    'BatchExplanationResponse',
    'SensitivityAnalysisRequest',
    'SensitivityAnalysisResponse',
    'FeatureComparisonRequest',
    'FeatureComparisonResponse',
    'RiskFactorAnalysisRequest',
    'RiskFactorAnalysisResponse',
    'ComparisonReportRequest',
    'ComparisonReportResponse',
    'SWOTAnalysisRequest',
    'SWOTAnalysisResponse',
    # Routes
    'router',
]
