from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.database.config import get_db
from app.auth.routes import get_current_user
from app.models.user import User
from app.models.entity import Entity
from app.models.document import Document
from app.extraction.models import ExtractionResult
from app.credit_scoring.credit_scoring_engine import CreditScoringEngine
from app.credit_scoring.models import CreditScore, CreditScoringHistory, UnderwritingDecision
from app.credit_scoring.schemas import (
    CreditScoringRequest,
    CreditScoringResponse,
    RiskDriver,
    CreditRecommendation,
)

router = APIRouter(prefix="/api/credit-scoring", tags=["Credit Scoring & Underwriting"])


def _to_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _merge_corrected_fields(extracted_data: dict, corrected_fields: dict) -> dict:
    if not isinstance(extracted_data, dict):
        return {}

    merged = dict(extracted_data)
    if not isinstance(corrected_fields, dict):
        return merged

    for section_key, section_updates in corrected_fields.items():
        if not isinstance(section_updates, dict):
            continue
        base_section = merged.get(section_key, {})
        if not isinstance(base_section, dict):
            base_section = {}
        updated_section = dict(base_section)
        updated_section.update(section_updates)
        merged[section_key] = updated_section
    return merged


def _get_best_extracted_data(db: Session, entity_id: int) -> dict:
    approved = (
        db.query(ExtractionResult)
        .filter(ExtractionResult.entity_id == entity_id, ExtractionResult.status == 'approved')
        .order_by(ExtractionResult.updated_at.desc())
        .first()
    )

    candidate = approved
    if not candidate:
        candidate = (
            db.query(ExtractionResult)
            .filter(ExtractionResult.entity_id == entity_id)
            .order_by(ExtractionResult.updated_at.desc())
            .first()
        )

    if not candidate:
        return {}

    raw_extracted = candidate.extracted_fields or {}
    corrected = candidate.corrected_fields or {}
    return _merge_corrected_fields(raw_extracted, corrected)


def _build_extracted_insights(extracted_data: dict) -> dict:
    income = extracted_data.get('income_statement', {}) if isinstance(extracted_data, dict) else {}
    balance = extracted_data.get('balance_sheet', {}) if isinstance(extracted_data, dict) else {}
    cash_flow = extracted_data.get('cash_flow', {}) if isinstance(extracted_data, dict) else {}

    revenue = _to_float(income.get('revenue'))
    net_income = _to_float(income.get('net_income'))
    current_assets = _to_float(balance.get('current_assets'))
    current_liabilities = _to_float(balance.get('current_liabilities'))
    total_liabilities = _to_float(balance.get('total_liabilities'))
    total_equity = _to_float(balance.get('equity') or balance.get('total_equity'))
    operating_cash_flow = _to_float(cash_flow.get('operating_cash_flow'))
    long_term_debt = _to_float(balance.get('long_term_debt')) or 0.0
    short_term_debt = _to_float(balance.get('short_term_debt')) or 0.0
    total_debt = long_term_debt + short_term_debt

    insights = {
        'primary_risk_drivers': [],
        'strength_areas': [],
        'improvement_areas': [],
    }

    if current_assets is not None and current_liabilities not in (None, 0):
        current_ratio = current_assets / current_liabilities
        if current_ratio < 1.0:
            insights['primary_risk_drivers'].append({
                'factor': 'Liquidity (Current Ratio)',
                'score': 35,
                'impact': 'High',
            })
        elif current_ratio >= 1.5:
            insights['strength_areas'].append({
                'factor': 'Liquidity Buffer',
                'score': 80,
            })
        else:
            insights['improvement_areas'].append({
                'factor': 'Liquidity (Current Ratio)',
                'score': 62,
                'potential_improvement': 13,
            })

    if total_liabilities is not None and total_equity not in (None, 0):
        debt_equity = total_liabilities / total_equity
        if debt_equity > 2.0:
            insights['primary_risk_drivers'].append({
                'factor': 'Leverage (Debt to Equity)',
                'score': 40,
                'impact': 'High',
            })
        elif debt_equity <= 1.2:
            insights['strength_areas'].append({
                'factor': 'Leverage Profile',
                'score': 78,
            })
        else:
            insights['improvement_areas'].append({
                'factor': 'Leverage Optimization',
                'score': 64,
                'potential_improvement': 11,
            })

    if revenue not in (None, 0) and net_income is not None:
        net_margin = net_income / revenue
        if net_margin < 0.05:
            insights['primary_risk_drivers'].append({
                'factor': 'Profitability (Net Margin)',
                'score': 45,
                'impact': 'Medium',
            })
        elif net_margin >= 0.12:
            insights['strength_areas'].append({
                'factor': 'Profitability Quality',
                'score': 82,
            })
        else:
            insights['improvement_areas'].append({
                'factor': 'Margin Improvement Potential',
                'score': 66,
                'potential_improvement': 9,
            })

    if operating_cash_flow is not None and total_debt > 0:
        coverage = operating_cash_flow / total_debt
        if coverage < 0.10:
            insights['primary_risk_drivers'].append({
                'factor': 'Debt Servicing Capacity',
                'score': 38,
                'impact': 'High',
            })
        elif coverage >= 0.25:
            insights['strength_areas'].append({
                'factor': 'Cash Flow Coverage',
                'score': 79,
            })

    # cap noise
    insights['primary_risk_drivers'] = insights['primary_risk_drivers'][:3]
    insights['strength_areas'] = insights['strength_areas'][:3]
    insights['improvement_areas'] = insights['improvement_areas'][:3]
    return insights


def _merge_insight_lists(existing: list, derived: list) -> list:
    merged = []
    seen = set()
    for item in (existing or []) + (derived or []):
        factor = str((item or {}).get('factor', '')).strip().lower()
        if not factor or factor in seen:
            continue
        seen.add(factor)
        merged.append(item)
    return merged[:3]


@router.post("/calculate", response_model=CreditScoringResponse)
async def calculate_credit_score(
    request: CreditScoringRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate comprehensive credit score for an entity.
    
    This endpoint:
    1. Validates entity and document existence
    2. Calls credit scoring engine with all input factors
    3. Calculates 8 component scores with proper weighting
    4. Generates final credit score (300-1000), PD, and risk category
    5. Provides underwriting recommendation
    6. Stores result for historical tracking
    
    Args:
        entity_id: ID of entity to score
        document_id: ID of supporting document
        financial_metrics: From FinancialMetricsEngine
        bank_relationship: Bank interaction data
        industry_data: Industry and market data
        management_quality: Management assessment
        collateral_data: Collateral details
        legal_compliance: Legal and regulatory data
        fraud_indicators: Fraud risk signals
        credit_bureau: Credit history and bureau data
    
    Returns:
        CreditScoringResponse with score, PD%, risk category, and recommendation
    """
    try:
        # Verify entity and document
        entity = db.query(Entity).filter(Entity.id == request.entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        document = db.query(Document).filter(Document.id == request.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify user is admin or analyst
        current_role = str(getattr(current_user, 'role', '')).lower()
        if current_role not in ['credit_analyst', 'admin', 'userrole.credit_analyst', 'userrole.admin']:
            raise HTTPException(status_code=403, detail="Unauthorized for credit scoring")
        
        # Initialize scoring engine
        engine = CreditScoringEngine()
        
        # Prepare inputs
        inputs = {
            'financial_metrics': request.financial_metrics,
            'bank_relationship_data': request.bank_relationship.dict() if request.bank_relationship else {},
            'industry_data': request.industry_data.dict() if request.industry_data else {},
            'management_quality_data': request.management_quality.dict() if request.management_quality else {},
            'collateral_data': request.collateral_data.dict() if request.collateral_data else {},
            'legal_compliance_data': request.legal_compliance.dict() if request.legal_compliance else {},
            'fraud_indicators': request.fraud_indicators.dict() if request.fraud_indicators else {},
            'credit_bureau_data': request.credit_bureau.dict() if request.credit_bureau else {},
        }
        
        # Calculate credit score
        result = engine.calculate_credit_score(inputs)
        
        if result.get('calculation_status') == 'error':
            raise HTTPException(status_code=400, detail=result.get('error_message', 'Scoring calculation failed'))
        
        # Store in database
        db_score = CreditScore(
            entity_id=request.entity_id,
            document_id=request.document_id,
            credit_score=result['credit_score'],
            probability_of_default=result['probability_of_default'],
            risk_category=result['risk_category'],
            financial_strength_score=result['component_scores'].get('financial_strength'),
            bank_relationship_score=result['component_scores'].get('bank_relationship'),
            industry_risk_score=result['component_scores'].get('industry_risk'),
            management_quality_score=result['component_scores'].get('management_quality'),
            collateral_strength_score=result['component_scores'].get('collateral_strength'),
            legal_risk_score=result['component_scores'].get('legal_risk'),
            fraud_risk_score=result['component_scores'].get('fraud_risk'),
            credit_bureau_score=result['component_scores'].get('credit_bureau_score'),
            component_scores_json=result['component_scores'],
            risk_drivers_json=result['risk_drivers'],
            decision=result['recommendation'].get('decision'),
            decision_rationale=result['recommendation'].get('rationale'),
            recommended_conditions=result['recommendation'].get('conditions'),
            recommended_rate_adjustment=result['recommendation'].get('recommended_rate_adjustment'),
        )
        db.add(db_score)
        db.commit()
        db.refresh(db_score)
        
        # Add to history
        history = CreditScoringHistory(
            entity_id=request.entity_id,
            credit_score=result['credit_score'],
            probability_of_default=result['probability_of_default'],
            risk_category=result['risk_category'],
            financial_strength_snapshot=result['component_scores'].get('financial_strength'),
            bank_relationship_snapshot=result['component_scores'].get('bank_relationship'),
            industry_risk_snapshot=result['component_scores'].get('industry_risk'),
            management_quality_snapshot=result['component_scores'].get('management_quality'),
        )
        db.add(history)
        db.commit()
        
        # Build response
        recommendation_data = result['recommendation']
        
        response = CreditScoringResponse(
            entity_id=request.entity_id,
            document_id=request.document_id,
            credit_score=result['credit_score'],
            probability_of_default=result['probability_of_default'],
            risk_category=result['risk_category'],
            component_scores=result['component_scores'],
            primary_risk_drivers=[
                RiskDriver(**driver) for driver in result['risk_drivers'].get('primary_risk_drivers', [])
            ],
            strength_areas=[
                RiskDriver(**area) for area in result['risk_drivers'].get('strength_areas', [])
            ],
            improvement_areas=[
                RiskDriver(**area) for area in result['risk_drivers'].get('improvement_areas', [])
            ],
            recommendation=CreditRecommendation(
                decision=recommendation_data.get('decision'),
                rationale=recommendation_data.get('rationale'),
                conditions=recommendation_data.get('conditions', []),
                specific_advice=recommendation_data.get('specific_advice'),
                recommended_rate_adjustment=recommendation_data.get('recommended_rate_adjustment', 0),
            ),
            calculation_status='success',
            warnings=result.get('warnings', []),
            errors=result.get('errors', []),
            calculated_at=datetime.utcnow(),
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Credit scoring failed: {str(e)}")


@router.get("/entity/{entity_id}", response_model=dict)
async def get_entity_credit_score(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the latest credit score for an entity.
    """
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        score = db.query(CreditScore).filter(
            CreditScore.entity_id == entity_id
        ).order_by(CreditScore.calculated_at.desc()).first()
        
        if not score:
            raise HTTPException(status_code=404, detail="No credit score found for this entity")

        stored_drivers = score.risk_drivers_json if isinstance(score.risk_drivers_json, dict) else {}
        extracted_data = _get_best_extracted_data(db, entity_id)
        extracted_insights = _build_extracted_insights(extracted_data)

        primary_risk_drivers = _merge_insight_lists(
            stored_drivers.get('primary_risk_drivers', []),
            extracted_insights.get('primary_risk_drivers', []),
        )
        strength_areas = _merge_insight_lists(
            stored_drivers.get('strength_areas', []),
            extracted_insights.get('strength_areas', []),
        )
        improvement_areas = _merge_insight_lists(
            stored_drivers.get('improvement_areas', []),
            extracted_insights.get('improvement_areas', []),
        )
        
        return {
            'entity_id': entity_id,
            'company_name': entity.company_name,
            'credit_score': score.credit_score,
            'probability_of_default': score.probability_of_default,
            'risk_category': score.risk_category,
            'component_scores': score.component_scores_json,
            'primary_risk_drivers': primary_risk_drivers,
            'strength_areas': strength_areas,
            'improvement_areas': improvement_areas,
            'decision': score.decision,
            'decision_rationale': score.decision_rationale,
            'approved_status': score.approval_status,
            'calculated_at': score.calculated_at,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve credit score: {str(e)}")


@router.get("/history/{entity_id}")
async def get_credit_score_history(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(12, ge=1, le=60),
):
    """
    Get historical credit scores for trend analysis.
    """
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        history = db.query(CreditScoringHistory).filter(
            CreditScoringHistory.entity_id == entity_id
        ).order_by(CreditScoringHistory.created_at.desc()).limit(limit).all()
        
        if not history:
            raise HTTPException(status_code=404, detail="No scoring history found")
        
        # Determine trend
        def calculate_trend(scores):
            if len(scores) < 2:
                return "insufficient_data"
            recent = scores[0]
            previous = scores[1] if len(scores) > 1 else scores[0]
            if recent > previous + 5:
                return "improving"
            elif recent < previous - 5:
                return "deteriorating"
            return "stable"
        
        scores = [h.credit_score for h in history]
        trend = calculate_trend(scores)
        
        return {
            'entity_id': entity_id,
            'company_name': entity.company_name,
            'history_count': len(history),
            'trend': trend,
            'scores': [
                {
                    'date': h.created_at,
                    'credit_score': h.credit_score,
                    'probability_of_default': h.probability_of_default,
                    'risk_category': h.risk_category,
                    'score_change': h.score_change,
                }
                for h in reversed(history)
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.post("/underwriting-decision")
async def create_underwriting_decision(
    credit_score_id: int,
    decision: str,
    decision_reason: str,
    proposed_interest_rate: float = None,
    proposed_loan_amount: float = None,
    approval_conditions: list = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record formal underwriting decision.
    
    Args:
        credit_score_id: ID of credit score being decided upon
        decision: APPROVED, DECLINED, PENDING_REVIEW, APPROVED_WITH_CONDITIONS
        decision_reason: Detailed reason for decision
        proposed_interest_rate: Annual interest rate %
        proposed_loan_amount: Loan amount in ₹
        approval_conditions: List of conditions if approved
    """
    try:
        # Verify user is authorized
        current_role = str(getattr(current_user, 'role', '')).lower()
        if current_role not in ['credit_analyst', 'admin', 'userrole.credit_analyst', 'userrole.admin']:
            raise HTTPException(status_code=403, detail="Unauthorized for underwriting decisions")
        
        credit_score = db.query(CreditScore).filter(CreditScore.id == credit_score_id).first()
        if not credit_score:
            raise HTTPException(status_code=404, detail="Credit score not found")
        
        # Create underwriting decision
        underwriting_decision = UnderwritingDecision(
            credit_score_id=credit_score_id,
            entity_id=credit_score.entity_id,
            decision=decision,
            decision_reason=decision_reason,
            reviewed_by=current_user.id,
            proposed_interest_rate=proposed_interest_rate,
            proposed_loan_amount=proposed_loan_amount,
            approval_conditions=approval_conditions or [],
        )
        
        db.add(underwriting_decision)
        
        # Update credit score status
        if decision == 'APPROVED':
            credit_score.approval_status = 'approved'
            credit_score.approved_by = current_user.id
        elif decision == 'DECLINED':
            credit_score.approval_status = 'rejected'
        elif decision == 'PENDING_REVIEW':
            credit_score.approval_status = 'review'
        
        credit_score.approval_notes = decision_reason
        
        db.commit()
        db.refresh(underwriting_decision)
        
        return {
            'id': underwriting_decision.id,
            'entity_id': underwriting_decision.entity_id,
            'decision': underwriting_decision.decision,
            'created_at': underwriting_decision.created_at,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create decision: {str(e)}")


@router.get("/recommendations/{entity_id}")
async def get_credit_recommendations(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed lending recommendations based on latest credit score.
    
    Returns:
    - Approval recommendation (APPROVE/CONDITIONAL/DECLINE)
    - Recommended loan terms
    - Required conditions if approved
    - Risk mitigation strategies
    - Monitoring parameters
    """
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        score = db.query(CreditScore).filter(
            CreditScore.entity_id == entity_id
        ).order_by(CreditScore.calculated_at.desc()).first()
        
        if not score:
            raise HTTPException(status_code=404, detail="No credit score found")
        
        # Generate recommendations based on credit score
        credit_score_value = score.credit_score
        
        if credit_score_value >= 850:
            action = "APPROVE"
            rationale = "Excellent credit profile with low default risk"
            conditions = []
            risk_factors = []
            mitigants = ["Strong financial position", "Excellent bank relationships", "Low industry risk"]
            monitoring = ["Quarterly financial reviews", "Annual bank relationship assessment"]
            recommended_rate_reduction = 200  # bps
            max_loan_amount = None  # No limit for excellent
            
        elif credit_score_value >= 750:
            action = "APPROVE"
            rationale = "Good credit profile with low default risk"
            conditions = ["Financial covenants on debt-to-equity ratio", "Annual financial audits"]
            risk_factors = []
            mitigants = ["Good liquidity position", "Stable bank relationships"]
            monitoring = ["Quarterly financial reviews", "Semi-annual credit monitoring"]
            recommended_rate_reduction = 100  # bps
            max_loan_amount = None
            
        elif credit_score_value >= 650:
            action = "APPROVE"
            rationale = "Acceptable credit profile with moderate risk"
            conditions = [
                "Personal guarantee from promoters",
                "Additional collateral required",
                "Quarterly reporting requirements",
                "Restrictive covenants on dividends"
            ]
            risk_factors = ["Moderate leverage", "Industry volatility"]
            mitigants = ["Acceptable management quality", "Reasonable collateral"]
            monitoring = ["Monthly financial reviews", "Regular credit monitoring", "Site inspections"]
            recommended_rate_reduction = 0  # No reduction, base rate
            annual_revenue = getattr(entity, 'annual_revenue', None) or getattr(entity, 'turnover', None)
            max_loan_amount = annual_revenue * 0.5 if annual_revenue else None
            
        elif credit_score_value >= 550:
            action = "CONDITIONAL"
            rationale = "Elevated credit risk - approval conditional on strong terms"
            conditions = [
                "Higher collateral requirement (120-150% LTV)",
                "Personal guarantee required",
                "Monthly financial reporting",
                "Quarterly management meetings",
                "Strict covenant compliance",
                "Insurance requirements"
            ]
            risk_factors = [
                "High leverage",
                "Industry headwinds",
                "Management concerns",
                "Weak collateral quality"
            ]
            mitigants = ["Adequate collateral coverage", "Manageable debt service"]
            monitoring = ["Monthly reviews", "Quarterly inspections", "Six-monthly credit review", "Covenant monitoring"]
            recommended_rate_reduction = -200  # 200 bps increase
            annual_revenue = getattr(entity, 'annual_revenue', None) or getattr(entity, 'turnover', None)
            max_loan_amount = annual_revenue * 0.25 if annual_revenue else None
            
        else:  # < 550
            action = "DECLINE"
            rationale = "Credit score indicates unacceptable risk level"
            conditions = ["Substantial improvements required"]
            risk_factors = [
                "Very high default probability",
                "Significant financial distress",
                "Poor bank relationships",
                "Regulatory or legal issues"
            ]
            mitigants = []
            monitoring = []
            recommended_rate_reduction = -500  # 500 bps increase (not applicable for decline)
            max_loan_amount = 0
        
        recommendations = {
            'entity_id': entity_id,
            'entity_name': entity.company_name,
            'score': {
                'credit_score': score.credit_score,
                'probability_of_default': score.probability_of_default,
                'risk_category': score.risk_category,
            },
            'action': action,
            'rationale': rationale,
            'conditions': conditions,
            'risk_factors': risk_factors,
            'risk_mitigants': mitigants,
            'monitoring_parameters': monitoring,
            'recommended_terms': [
                {
                    'parameter': 'Interest Rate Adjustment',
                    'value': f"{'+' if recommended_rate_reduction > 0 else ''}{recommended_rate_reduction} basis points"
                },
                {
                    'parameter': 'Maximum Loan Amount',
                    'value': f"₹{max_loan_amount:.2f}L" if max_loan_amount else "No Limit"
                },
                {
                    'parameter': 'Preferred Tenor',
                    'value': "12-60 months" if action != "DECLINE" else "N/A"
                },
                {
                    'parameter': 'Review Frequency',
                    'value': "Quarterly" if action == "APPROVE" else "Monthly" if action == "CONDITIONAL" else "N/A"
                }
            ],
            'generated_at': datetime.utcnow(),
        }
        
        return recommendations
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")


@router.get("/scoring-methodology")
async def get_scoring_methodology():
    """Get detailed information about credit scoring methodology."""
    return {
        'scoring_engine': 'CreditScoringEngine v1.0',
        'scale': {
            'min': 300,
            'max': 1000,
            'description': 'Credit score scale from very high risk to very low risk'
        },
        'components': [
            {
                'name': 'Financial Strength',
                'weight': 0.20,
                'factors': [
                    'Profitability (30%)',
                    'Liquidity (30%)',
                    'Solvency (40%)'
                ],
                'scale': '0-100'
            },
            {
                'name': 'Bank Relationship',
                'weight': 0.15,
                'factors': [
                    'Years of relationship',
                    'Transaction volume',
                    'Credit facility utilization',
                    'Overdraft history',
                    'Payment timeliness'
                ],
                'scale': '0-100'
            },
            {
                'name': 'Industry Risk',
                'weight': 0.15,
                'factors': [
                    'Sector risk profile',
                    'Market position',
                    'Growth trajectory',
                    'Economic sensitivity'
                ],
                'scale': '0-100'
            },
            {
                'name': 'Management Quality',
                'weight': 0.10,
                'factors': [
                    'Experience',
                    'Education',
                    'Track record',
                    'Industry expertise',
                    'Compliance history'
                ],
                'scale': '0-100'
            },
            {
                'name': 'Collateral Strength',
                'weight': 0.10,
                'factors': [
                    'Collateral to loan ratio',
                    'Quality of collateral',
                    'Liquidity of collateral'
                ],
                'scale': '0-100'
            },
            {
                'name': 'Legal Risk',
                'weight': 0.10,
                'factors': [
                    'Entity status',
                    'Regulatory compliance',
                    'Litigation history',
                    'Regulatory violations',
                    'Bankruptcy history'
                ],
                'scale': '0-100'
            },
            {
                'name': 'Fraud Risk',
                'weight': 0.10,
                'factors': [
                    'Fraud investigation history',
                    'Document authenticity',
                    'Financial consistency',
                    'Identity verification',
                    'Red flags'
                ],
                'scale': '0-100'
            },
            {
                'name': 'Credit Bureau Score',
                'weight': 0.10,
                'factors': [
                    'Credit bureau score',
                    'Payment default history',
                    'Credit utilization',
                    'Credit age'
                ],
                'scale': '0-100'
            }
        ],
        'risk_categories': {
            'EXCELLENT': {
                'score_range': '850-1000',
                'pd_range': '0.05%-0.50%',
                'meaning': 'Very low default risk'
            },
            'VERY_GOOD': {
                'score_range': '750-849',
                'pd_range': '0.50%-1.00%',
                'meaning': 'Low default risk'
            },
            'GOOD': {
                'score_range': '650-749',
                'pd_range': '1.00%-2.50%',
                'meaning': 'Moderate-low default risk'
            },
            'FAIR': {
                'score_range': '550-649',
                'pd_range': '2.50%-5.00%',
                'meaning': 'Moderate default risk'
            },
            'POOR': {
                'score_range': '450-549',
                'pd_range': '5.00%-10.00%',
                'meaning': 'High default risk'
            },
            'VERY_POOR': {
                'score_range': '300-449',
                'pd_range': '10.00%-25.00%',
                'meaning': 'Very high default risk'
            },
            'UNACCEPTABLE': {
                'score_range': '0-299',
                'pd_range': '25.00%-100.00%',
                'meaning': 'Unacceptable risk'
            }
        },
        'decision_rules': {
            'EXCELLENT': 'Approved - Low risk',
            'VERY_GOOD': 'Approved - Low risk',
            'GOOD': 'Approved - Standard conditions',
            'FAIR': 'Approved with enhanced conditions',
            'POOR': 'Approved with strong conditions or Declined',
            'VERY_POOR': 'Declined or Substantial conditions',
            'UNACCEPTABLE': 'Decline recommended'
        }
    }


def calculate_weighted_score(component_scores: dict) -> int:
    """Helper to calculate final score from components"""
    weighted = (
        component_scores.get('financial_strength', 50) * 0.20 +
        component_scores.get('bank_relationship', 50) * 0.15 +
        component_scores.get('industry_risk', 50) * 0.15 +
        component_scores.get('management_quality', 50) * 0.10 +
        component_scores.get('collateral_strength', 50) * 0.10 +
        component_scores.get('legal_risk', 50) * 0.10 +
        component_scores.get('fraud_risk', 50) * 0.10 +
        component_scores.get('credit_bureau_score', 50) * 0.10
    )
    return int(300 + (weighted * 7))
