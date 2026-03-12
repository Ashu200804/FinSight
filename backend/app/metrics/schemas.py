from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class FinancialMetricsRequest(BaseModel):
    """Request to calculate financial metrics"""
    document_id: int = Field(..., description="Document ID to process")
    use_extracted_data: bool = Field(default=True, description="Use extracted data from AI pipeline")
    

class RatioValue(BaseModel):
    """Individual ratio calculation result"""
    value: Optional[float] = Field(None, description="Calculated ratio value")
    unit: Optional[str] = Field(None, description="Unit of measurement (%):%', 'ratio', 'currency', 'times', 'days')")
    interpretation: Optional[str] = Field(None, description="What this ratio means")
    status: Optional[str] = Field(None, description="success, error, or pending")
    reason: Optional[str] = Field(None, description="Error reason if status is error")
    benchmark: Optional[str] = Field(None, description="Industry benchmark")
    warning: Optional[str] = Field(None, description="Warning message if applicable")


class ProfitabilityRatios(BaseModel):
    """Profitability metrics"""
    profit_margin: Optional[RatioValue] = None
    gross_profit_margin: Optional[RatioValue] = None
    ebitda_margin: Optional[RatioValue] = None
    return_on_assets: Optional[RatioValue] = None
    return_on_equity: Optional[RatioValue] = None


class LiquidityRatios(BaseModel):
    """Liquidity metrics"""
    current_ratio: Optional[RatioValue] = None
    quick_ratio: Optional[RatioValue] = None
    cash_ratio: Optional[RatioValue] = None
    working_capital: Optional[RatioValue] = None
    working_capital_ratio: Optional[RatioValue] = None


class SolvencyRatios(BaseModel):
    """Solvency metrics"""
    debt_to_equity: Optional[RatioValue] = None
    debt_to_assets: Optional[RatioValue] = None
    equity_ratio: Optional[RatioValue] = None
    interest_coverage: Optional[RatioValue] = None
    debt_service_coverage: Optional[RatioValue] = None


class EfficiencyRatios(BaseModel):
    """Operational efficiency metrics"""
    asset_turnover: Optional[RatioValue] = None
    inventory_turnover: Optional[RatioValue] = None
    receivables_turnover: Optional[RatioValue] = None
    days_sales_outstanding: Optional[RatioValue] = None


class Score(BaseModel):
    """Score with assessment"""
    score: float = Field(..., description="Score value")
    max_score: float = Field(..., description="Maximum possible score")
    assessment: str = Field(..., description="Excellent, Good, Fair, Poor, Very Poor")


class CreditScoreInputs(BaseModel):
    """Inputs for credit scoring engine"""
    profitability_score: Score
    liquidity_score: Score
    solvency_score: Score
    efficiency_score: Score
    cash_flow_health: Dict[str, Any]
    leverage_assessment: Dict[str, str]
    trend_indicators: Dict[str, Any]


class FinancialMetricsResponse(BaseModel):
    """Complete financial metrics response"""
    document_id: int
    entity_id: int
    calculated_at: datetime
    
    # Extracted metrics
    extracted_metrics: Dict[str, Optional[float]] = Field(..., description="Extracted financial metrics")
    
    # Calculated ratios
    profitability_ratios: ProfitabilityRatios
    liquidity_ratios: LiquidityRatios
    solvency_ratios: SolvencyRatios
    efficiency_ratios: EfficiencyRatios
    
    # Credit scoring inputs
    credit_score_inputs: CreditScoreInputs
    
    # Status information
    calculation_status: str = Field(..., description="success, partial, or error")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    errors: List[str] = Field(default_factory=list, description="Fatal errors encountered")


class FinancialMetricsStored(BaseModel):
    """Financial metrics as stored in database"""
    id: int
    document_id: int
    entity_id: int
    metrics_json: Dict[str, Any]
    profitability_score: float
    liquidity_score: float
    solvency_score: float
    efficiency_score: float
    overall_health_score: float
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
