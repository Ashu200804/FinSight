"""
API routes for explainability endpoints.

Provides endpoints for generating and retrieving credit decision explanations
using SHAP-based analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import logging

from app.database.config import get_db
from app.auth.routes import get_current_user
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
    ExplanationReviewRequest,
    ExplanationReviewResponse,
    SWOTAnalysisRequest,
    SWOTAnalysisResponse,
    RiskFactorResponse,
    FeatureImportanceResponse,
    CreditDecisionEnum,
)
from app.explainability.models import (
    ExplanationModel,
    FeatureImportanceModel,
    RiskFactorModel,
    ExplanationAuditLog,
)
from app.explainability.explainability_engine import (
    SHAPExplainer,
    CreditDecisionExplainer,
    CreditDecisionExplanation,
    SWOTLLMGenerator,
)
from app.models.entity import Entity

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/api/explainability",
    tags=["Explainability & SHAP Analysis"],
)

# Global explainers (in production, load trained models)
shap_explainer = None
credit_explainer = None
swot_generator = None


def _format_supporting_metrics(feature_contributions) -> dict:
    formatted = {}
    if not feature_contributions:
        return formatted

    for item in feature_contributions:
        if not isinstance(item, dict):
            continue
        feature_name = item.get("feature")
        contribution_value = item.get("contribution")
        if feature_name is None or contribution_value is None:
            continue
        try:
            formatted[str(feature_name)] = float(contribution_value)
        except (TypeError, ValueError):
            continue

    return formatted


def get_explainers():
    """Get or initialize explainers"""
    global shap_explainer, credit_explainer
    
    if not shap_explainer or not credit_explainer:
        # Import here to avoid circular imports
        from app.explainability.explainability_engine import create_mock_explainer
        shap_explainer, credit_explainer = create_mock_explainer()
    
    return shap_explainer, credit_explainer


def get_swot_generator() -> SWOTLLMGenerator:
    """Get or initialize SWOT LLM generator"""
    global swot_generator

    if not swot_generator:
        swot_generator = SWOTLLMGenerator()

    return swot_generator


@router.post(
    "/explain-decision",
    response_model=ExplanationResponse,
    summary="Generate explanation for credit decision",
    description="Generate SHAP-based explanation for a credit decision with feature importance and risk factors"
)
async def explain_credit_decision(
    request: ExplanationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Generate comprehensive explanation for a credit decision.
    
    - Analyzes feature importance using SHAP
    - Identifies risk factors
    - Provides human-readable reasoning
    - Performs sensitivity analysis
    """
    try:
        # Get explainers
        shap_exp, credit_exp = get_explainers()
        
        # Convert features to DataFrame
        X = pd.DataFrame([request.features], columns=request.feature_names)
        if getattr(shap_exp, "feature_names", None):
            X = X.reindex(columns=shap_exp.feature_names, fill_value=0.0)
        
        # Get entity name
        entity = db.query(Entity).filter(Entity.id == request.entity_id).first()
        applicant_name = entity.company_name if entity else "Unknown"
        
        # Generate explanation
        explanation = credit_exp.explain_credit_decision(
            decision_id=f"EXP-{request.entity_id}-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}",
            applicant_name=applicant_name,
            X=X,
            credit_score=request.credit_score,
            credit_rating=request.credit_rating,
            decision=request.decision,
            metrics=request.metrics,
            research_findings=request.research_findings
        )
        
        if request.credit_decision_id is not None:
            try:
                db_explanation = ExplanationModel(
                    credit_decision_id=request.credit_decision_id,
                    entity_id=request.entity_id,
                    decision=request.decision,
                    credit_score=request.credit_score,
                    credit_rating=request.credit_rating,
                    decision_confidence=explanation.decision_confidence,
                    executive_summary=explanation.executive_summary,
                    explanation_confidence=explanation.explanation_confidence,
                    shap_values=explanation.feature_importance,
                    key_findings=explanation.key_findings,
                    strengths=explanation.strengths,
                    concerns=explanation.concerns,
                    recommendations=explanation.recommendations,
                    sensitivity_analysis=explanation.sensitivity_analysis,
                    model_version=request.model_version,
                    model_type=request.model_type,
                    created_by=current_user.id
                )

                db.add(db_explanation)

                for fi in explanation.feature_importance:
                    feature_imp = FeatureImportanceModel(
                        explanation=db_explanation,
                        feature_name=fi['feature_name'],
                        shap_value=fi['contribution'],
                        importance_score=fi['importance_score'],
                        direction=fi['direction'],
                        impact_level=fi['impact_level'],
                        rank=explanation.feature_importance.index(fi) + 1
                    )
                    db.add(feature_imp)

                for rf in explanation.top_risk_factors:
                    risk_factor = RiskFactorModel(
                        explanation=db_explanation,
                        factor_name=rf.factor_name,
                        severity=rf.severity,
                        description=rf.description,
                        recommendation=rf.recommendation,
                        supporting_metrics=_format_supporting_metrics(rf.feature_contributions)
                    )
                    db.add(risk_factor)

                db.commit()
            except Exception as db_error:
                db.rollback()
                logger.warning(f"Explainability persistence skipped: {db_error}")
        
        # Convert to response
        response = ExplanationResponse(
            decision_id=explanation.decision_id,
            applicant_name=explanation.applicant_name,
            final_score=explanation.final_score,
            final_rating=explanation.final_rating,
            decision=explanation.decision,
            decision_confidence=explanation.decision_confidence,
            feature_importance=[
                FeatureImportanceResponse(
                    feature_name=fi['feature_name'],
                    importance_score=fi['importance_score'],
                    contribution=fi['contribution'],
                    direction=fi['direction'],
                    impact_level=fi['impact_level']
                )
                for fi in explanation.feature_importance
            ],
            top_contributing_factors=explanation.top_contributing_factors,
            top_risk_factors=[
                RiskFactorResponse(
                    factor_name=rf.factor_name,
                    severity=rf.severity,
                    description=rf.description,
                    recommendation=rf.recommendation,
                    supporting_metrics=_format_supporting_metrics(rf.feature_contributions) or None
                )
                for rf in explanation.top_risk_factors
            ],
            executive_summary=explanation.executive_summary,
            key_findings=explanation.key_findings,
            strengths=explanation.strengths,
            concerns=explanation.concerns,
            recommendations=explanation.recommendations,
            sensitivity_analysis=explanation.sensitivity_analysis,
            generated_at=explanation.generated_at,
            explanation_confidence=explanation.explanation_confidence
        )
        
        logger.info(f"Generated explanation for entity {request.entity_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")


@router.get(
    "/explanation/{explanation_id}",
    response_model=ExplanationResponse,
    summary="Get stored explanation",
    description="Retrieve a previously generated explanation"
)
async def get_explanation(
    explanation_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a stored explanation by ID"""
    try:
        explanation = db.query(ExplanationModel).filter(
            ExplanationModel.id == explanation_id
        ).first()
        
        if not explanation:
            raise HTTPException(status_code=404, detail="Explanation not found")
        
        # Convert to response
        response = ExplanationResponse(
            decision_id=f"EXP-{explanation.id}",
            applicant_name=None,
            final_score=explanation.credit_score,
            final_rating=explanation.credit_rating,
            decision=explanation.decision,
            decision_confidence=explanation.decision_confidence,
            feature_importance=[
                FeatureImportanceResponse(
                    feature_name=fi.feature_name,
                    importance_score=fi.importance_score,
                    contribution=fi.shap_value,
                    direction=fi.direction,
                    impact_level=fi.impact_level
                )
                for fi in explanation.feature_importances
            ],
            top_contributing_factors=[],
            top_risk_factors=[
                RiskFactorResponse(
                    factor_name=rf.factor_name,
                    severity=rf.severity,
                    description=rf.description,
                    recommendation=rf.recommendation,
                    supporting_metrics=rf.supporting_metrics
                )
                for rf in explanation.risk_factors
            ],
            executive_summary=explanation.executive_summary,
            key_findings=explanation.key_findings or [],
            strengths=explanation.strengths or [],
            concerns=explanation.concerns or [],
            recommendations=explanation.recommendations or [],
            sensitivity_analysis=explanation.sensitivity_analysis or {},
            generated_at=explanation.created_at.isoformat(),
            explanation_confidence=explanation.explanation_confidence
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving explanation: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving explanation")


@router.get(
    "/entity/{entity_id}/latest-explanation",
    response_model=ExplanationResponse,
    summary="Get latest explanation for entity",
    description="Retrieve the most recent explanation generated for an entity"
)
async def get_latest_explanation(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the latest explanation for an entity"""
    try:
        explanation = db.query(ExplanationModel).filter(
            ExplanationModel.entity_id == entity_id
        ).order_by(ExplanationModel.created_at.desc()).first()
        
        if not explanation:
            raise HTTPException(status_code=404, detail="No explanation found for this entity")
        
        # Convert to response (similar to get_explanation)
        response = ExplanationResponse(
            decision_id=f"EXP-{explanation.id}",
            applicant_name=None,
            final_score=explanation.credit_score,
            final_rating=explanation.credit_rating,
            decision=explanation.decision,
            decision_confidence=explanation.decision_confidence,
            feature_importance=[
                FeatureImportanceResponse(
                    feature_name=fi.feature_name,
                    importance_score=fi.importance_score,
                    contribution=fi.shap_value,
                    direction=fi.direction,
                    impact_level=fi.impact_level
                )
                for fi in explanation.feature_importances
            ],
            top_contributing_factors=[],
            top_risk_factors=[
                RiskFactorResponse(
                    factor_name=rf.factor_name,
                    severity=rf.severity,
                    description=rf.description,
                    recommendation=rf.recommendation,
                    supporting_metrics=rf.supporting_metrics
                )
                for rf in explanation.risk_factors
            ],
            executive_summary=explanation.executive_summary,
            key_findings=explanation.key_findings or [],
            strengths=explanation.strengths or [],
            concerns=explanation.concerns or [],
            recommendations=explanation.recommendations or [],
            sensitivity_analysis=explanation.sensitivity_analysis or {},
            generated_at=explanation.created_at.isoformat(),
            explanation_confidence=explanation.explanation_confidence
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving latest explanation: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving explanation")


@router.post(
    "/sensitivity-analysis",
    response_model=SensitivityAnalysisResponse,
    summary="Perform sensitivity analysis",
    description="Analyze how credit score changes with variations in key metrics"
)
async def sensitivity_analysis(
    request: SensitivityAnalysisRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Perform sensitivity analysis on a credit decision.
    
    Shows how the credit score and decision would change with different
    input values for a specific metric.
    """
    try:
        # Get the explanation
        explanation = db.query(ExplanationModel).filter(
            ExplanationModel.decision_id == request.decision_id
        ).first()
        
        if not explanation:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        sensitivity = explanation.sensitivity_analysis or {}
        metric_data = sensitivity.get(request.metric_name, {})
        
        if not metric_data:
            raise HTTPException(status_code=400, detail=f"Metric {request.metric_name} not found in analysis")
        
        # Build analysis results
        analysis = {}
        base_value = metric_data.get('base_value', 0)
        elasticity = metric_data.get('elasticity', 0.8)
        base_score = explanation.credit_score
        
        for var_pct in request.variation_percentages:
            # Calculate score change based on elasticity
            pct_change = var_pct / 100.0
            score_change = base_score * elasticity * pct_change
            new_score = base_score + score_change
            analysis[str(var_pct)] = max(0, min(1000, new_score))  # Cap between 0-1000
        
        return SensitivityAnalysisResponse(
            decision_id=request.decision_id,
            metric_name=request.metric_name,
            base_value=base_value,
            base_score=base_score,
            analysis=analysis,
            elasticity=elasticity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing sensitivity analysis: {e}")
        raise HTTPException(status_code=500, detail="Error performing sensitivity analysis")


@router.post(
    "/risk-factor-analysis",
    response_model=RiskFactorAnalysisResponse,
    summary="Analyze risk factors",
    description="Perform comprehensive risk factor analysis for an entity"
)
async def analyze_risk_factors(
    request: RiskFactorAnalysisRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Perform risk factor analysis for an entity"""
    try:
        # Get latest explanation for entity
        explanation = db.query(ExplanationModel).filter(
            ExplanationModel.entity_id == request.entity_id
        ).order_by(ExplanationModel.created_at.desc()).first()
        
        if not explanation:
            raise HTTPException(status_code=404, detail="No explanation found for entity")
        
        # Categorize risk factors by severity
        risk_factors = explanation.risk_factors
        
        critical = [RiskFactorResponse(
            factor_name=rf.factor_name,
            severity=rf.severity,
            description=rf.description,
            recommendation=rf.recommendation
        ) for rf in risk_factors if rf.severity == 'CRITICAL']
        
        high = [RiskFactorResponse(
            factor_name=rf.factor_name,
            severity=rf.severity,
            description=rf.description,
            recommendation=rf.recommendation
        ) for rf in risk_factors if rf.severity == 'HIGH']
        
        medium = [RiskFactorResponse(
            factor_name=rf.factor_name,
            severity=rf.severity,
            description=rf.description,
            recommendation=rf.recommendation
        ) for rf in risk_factors if rf.severity == 'MEDIUM']
        
        # Calculate aggregate risk score (0-100)
        severity_weights = {'CRITICAL': 25, 'HIGH': 15, 'MEDIUM': 8, 'LOW': 3}
        aggregate_score = min(100, sum(
            severity_weights.get(rf.severity, 0)
            for rf in risk_factors
        ))
        
        return RiskFactorAnalysisResponse(
            entity_id=request.entity_id,
            total_risk_factors=len(risk_factors),
            critical_risks=critical,
            high_risks=high,
            medium_risks=medium,
            aggregate_risk_score=aggregate_score,
            risk_trend="STABLE"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing risk factors: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing risk factors")


@router.post(
    "/batch-explanations",
    response_model=BatchExplanationResponse,
    summary="Generate batch explanations",
    description="Generate explanations for multiple entities"
)
async def batch_explanations(
    request: BatchExplanationRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate explanations for multiple entities (batch operation)"""
    try:
        explanations = []
        
        for entity_id in request.entity_ids:
            explanation = db.query(ExplanationModel).filter(
                ExplanationModel.entity_id == entity_id
            ).order_by(ExplanationModel.created_at.desc()).first()
            
            if explanation:
                summary = ExplanationSummaryResponse(
                    decision_id=f"EXP-{explanation.id}",
                    entity_id=explanation.entity_id,
                    credit_rating=explanation.credit_rating,
                    decision=explanation.decision,
                    decision_confidence=explanation.decision_confidence,
                    top_contributing_factors=[],
                    generated_at=explanation.created_at.isoformat(),
                    explanation_confidence=explanation.explanation_confidence
                )
                explanations.append(summary)
        
        return BatchExplanationResponse(
            total_explanations=len(explanations),
            explanations=explanations,
            generated_at=pd.Timestamp.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in batch explanations: {e}")
        raise HTTPException(status_code=500, detail="Error generating batch explanations")


@router.get(
    "/feature-importance/{entity_id}",
    response_model=List[FeatureImportanceResponse],
    summary="Get feature importance",
    description="Get feature importance for latest explanation of an entity"
)
async def get_feature_importance(
    entity_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get feature importance ranking for an entity"""
    try:
        explanation = db.query(ExplanationModel).filter(
            ExplanationModel.entity_id == entity_id
        ).order_by(ExplanationModel.created_at.desc()).first()
        
        if not explanation:
            raise HTTPException(status_code=404, detail="No explanation found for entity")
        
        feature_importances = db.query(FeatureImportanceModel).filter(
            FeatureImportanceModel.explanation_id == explanation.id
        ).order_by(FeatureImportanceModel.importance_score.desc()).limit(limit).all()
        
        return [
            FeatureImportanceResponse(
                feature_name=fi.feature_name,
                importance_score=fi.importance_score,
                contribution=fi.shap_value,
                direction=fi.direction,
                impact_level=fi.impact_level
            )
            for fi in feature_importances
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feature importance: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving feature importance")


@router.post(
    "/swot-analysis",
    response_model=SWOTAnalysisResponse,
    summary="Generate LLM SWOT analysis",
    description="Generate SWOT analysis from financial metrics, market sentiment, and industry data"
)
async def generate_swot_analysis(
    request: SWOTAnalysisRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate SWOT analysis using LLM with deterministic fallback."""
    try:
        generator = get_swot_generator()
        swot = generator.generate_swot(
            company_name=request.company_name,
            financial_metrics=request.financial_metrics,
            market_sentiment=request.market_sentiment,
            industry_data=request.industry_data,
            model=request.model
        )

        return SWOTAnalysisResponse(**swot)

    except Exception as e:
        logger.error(f"Error generating SWOT analysis: {e}")
        raise HTTPException(status_code=500, detail="Error generating SWOT analysis")


@router.get(
    "/health",
    summary="Check explainability service health",
    description="Health check endpoint for the explainability service"
)
async def health_check():
    """Health check for explainability service"""
    try:
        shap_exp, credit_exp = get_explainers()
        return {
            "status": "healthy",
            "shap_initialized": shap_exp is not None,
            "credit_explainer_initialized": credit_exp is not None
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
