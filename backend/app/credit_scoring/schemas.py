from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Input Schemas

class BankRelationshipInput(BaseModel):
    """Bank relationship data"""
    relationship_years: int = Field(default=0, description="Years of relationship with bank")
    avg_monthly_transaction_volume: float = Field(default=0, description="Average monthly transaction volume (₹)")
    credit_facility_utilization: float = Field(default=0.5, description="Utilization ratio (0-1)")
    overdraft_incidents_6m: int = Field(default=0, description="Number of overdraft incidents in 6 months")
    avg_payment_delay_days: int = Field(default=0, description="Average payment delay in days")


class IndustryInput(BaseModel):
    """Industry and market data"""
    sector: str = Field(default="IT", description="Industry sector")
    market_position: float = Field(default=0.5, description="Market position strength (0-1)")
    growth_trajectory: float = Field(default=0.5, description="Growth trajectory (0-1)")
    economic_sensitivity: float = Field(default=0.5, description="Economic sensitivity (0-1)")


class ManagementQualityInput(BaseModel):
    """Management quality data"""
    avg_experience_years: int = Field(default=5, description="Average experience of key managers")
    postgraduate_percentage: float = Field(default=50, description="% of management with postgraduate degree")
    previous_ventures_success_rate: float = Field(default=0.5, description="Success rate of previous ventures (0-1)")
    industry_experience_years: int = Field(default=5, description="Years of experience in same industry")
    compliance_record_score: float = Field(default=0.5, description="Regulatory compliance record (0-1)")


class CollateralInput(BaseModel):
    """Collateral details"""
    loan_amount: float = Field(..., description="Requested loan amount (₹)")
    collateral_value: float = Field(default=0, description="Total collateral value (₹)")
    collateral_type: str = Field(default="UNSECURED", description="Type of collateral")
    liquidation_days: int = Field(default=365, description="Days to liquidate collateral")


class LegalInput(BaseModel):
    """Legal and regulatory data"""
    entity_status: str = Field(default="ACTIVE", description="Legal entity status")
    regulatory_compliance_score: float = Field(default=0.7, description="Compliance score (0-1)")
    active_litigation_cases: int = Field(default=0, description="Active litigation cases")
    regulatory_violations_count: int = Field(default=0, description="Regulatory violations in last 5 years")
    bankruptcy_days_ago: int = Field(default=10000, description="Days since last bankruptcy (or 10000+ if none)")


class FraudInput(BaseModel):
    """Fraud risk indicators"""
    fraud_investigations_count: int = Field(default=0, description="Number of fraud investigations")
    document_authenticity_score: float = Field(default=1.0, description="Document authenticity (0-1)")
    financial_consistency_score: float = Field(default=1.0, description="Financial statement consistency (0-1)")
    identity_verification_score: float = Field(default=1.0, description="Identity verification score (0-1)")
    red_flags_count: int = Field(default=0, description="Number of red flags detected")


class CreditBureauInput(BaseModel):
    """Credit bureau and payment history"""
    credit_bureau_score: Optional[int] = Field(None, description="Credit bureau score (300-900)")
    payment_defaults_24m: int = Field(default=0, description="Payment defaults in last 24 months")
    credit_utilization_ratio: float = Field(default=0.5, description="Credit utilization ratio (0-1)")
    credit_age_months: int = Field(default=12, description="Credit age in months")


class CreditScoringRequest(BaseModel):
    """Complete credit scoring request"""
    entity_id: int = Field(..., description="Entity ID")
    document_id: int = Field(..., description="Document ID from vault")
    financial_metrics: Dict[str, Any] = Field(..., description="From FinancialMetricsEngine")
    bank_relationship: Optional[BankRelationshipInput] = Field(default_factory=BankRelationshipInput)
    industry_data: Optional[IndustryInput] = Field(default_factory=IndustryInput)
    management_quality: Optional[ManagementQualityInput] = Field(default_factory=ManagementQualityInput)
    collateral_data: Optional[CollateralInput] = Field(None)
    legal_compliance: Optional[LegalInput] = Field(default_factory=LegalInput)
    fraud_indicators: Optional[FraudInput] = Field(default_factory=FraudInput)
    credit_bureau: Optional[CreditBureauInput] = Field(default_factory=CreditBureauInput)


# Output Schemas

class ComponentScore(BaseModel):
    """Individual component score"""
    score: int = Field(..., description="Score 0-100")
    weight: float = Field(..., description="Weight in final score (proportion)")
    assessment: Optional[str] = Field(None, description="Assessment text")


class RiskDriver(BaseModel):
    """Risk driver details"""
    factor: str = Field(..., description="Risk factor name")
    score: int = Field(..., description="Factor score")
    impact: Optional[str] = Field(None, description="Impact level: High, Medium, Low")
    potential_improvement: Optional[int] = Field(None, description="Points that can be improved")


class CreditRecommendation(BaseModel):
    """Credit decision recommendation"""
    decision: str = Field(..., description="APPROVED, APPROVED_WITH_CONDITIONS, DECLINED, etc.")
    rationale: str = Field(..., description="Reason for decision")
    conditions: List[str] = Field(default_factory=list, description="Conditions if approved")
    specific_advice: Optional[str] = Field(None, description="Specific guidance")
    recommended_rate_adjustment: int = Field(default=0, description="Rate adjustment in basis points")


class CreditScoringResponse(BaseModel):
    """Complete credit scoring response"""
    entity_id: int
    document_id: int
    credit_score: int = Field(..., description="Final score 300-1000")
    probability_of_default: float = Field(..., description="PD percentage (0-100)")
    risk_category: str = Field(..., description="Risk category (EXCELLENT to UNACCEPTABLE)")
    
    # Component scores
    component_scores: Dict[str, int] = Field(..., description="Individual component scores (0-100)")
    
    # Risk assessment
    primary_risk_drivers: List[RiskDriver] = Field(default_factory=list)
    strength_areas: List[RiskDriver] = Field(default_factory=list)
    improvement_areas: List[RiskDriver] = Field(default_factory=list)
    
    # Recommendation
    recommendation: CreditRecommendation
    
    # Status
    calculation_status: str = Field(default="success")
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    calculated_at: datetime


class CreditScoreStored(BaseModel):
    """Credit score as stored in database"""
    id: int
    entity_id: int
    document_id: int
    metrics_id: Optional[int] = None
    
    credit_score: int
    probability_of_default: float
    risk_category: str
    
    financial_score: Optional[float] = None
    risk_score: Optional[float] = None
    credit_grade: Optional[str] = None
    
    scoring_factors_json: Optional[Dict[str, Any]] = None
    risk_assessment_json: Optional[Dict[str, Any]] = None
    
    approval_status: Optional[str] = None
    approval_notes: Optional[str] = None
    
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CreditScoreComparison(BaseModel):
    """For comparing historical scores"""
    dates: List[datetime]
    credit_scores: List[int]
    risk_categories: List[str]
    probability_of_defaults: List[float]
    trend: str = Field(..., description="improving, deteriorating, stable")
