"""
Research Engine Pydantic Schemas

Validation schemas for research API inputs/outputs
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class SentimentEnum(str, Enum):
    POSITIVE = 'POSITIVE'
    NEGATIVE = 'NEGATIVE'
    NEUTRAL = 'NEUTRAL'


class RiskLevelEnum(str, Enum):
    NONE = 'NONE'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


class ComplianceStatusEnum(str, Enum):
    COMPLIANT = 'COMPLIANT'
    NEEDS_REVIEW = 'NEEDS_REVIEW'
    NON_COMPLIANT = 'NON_COMPLIANT'
    UNDER_INVESTIGATION = 'UNDER_INVESTIGATION'


# News Article Schema
class NewsArticleBase(BaseModel):
    title: str = Field(..., max_length=500)
    source: str = Field(..., max_length=255)
    published_at: datetime
    url: HttpUrl
    description: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    sentiment: SentimentEnum
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    news_type: str = Field(..., max_length=50)
    relevance_score: Optional[float] = Field(None, ge=0, le=1)


class NewsArticleCreate(NewsArticleBase):
    entity_id: int


class NewsArticleResponse(NewsArticleBase):
    id: int
    entity_id: int
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class NewsSearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)
    days_back: int = Field(30, ge=1, le=365)
    sentiment_filter: Optional[SentimentEnum] = None
    limit: int = Field(50, ge=1, le=200)


class NewsSearchResponse(BaseModel):
    company_name: str
    search_period_days: int
    total_articles_found: int
    articles: List[NewsArticleResponse]
    sentiment_breakdown: Dict[str, float]  # POSITIVE, NEGATIVE, NEUTRAL percentages
    trend: str  # POSITIVE, NEUTRAL, NEGATIVE
    trending_topics: List[str]
    searched_at: datetime


# Legal Filing Schema
class LegalFilingBase(BaseModel):
    filing_type: str = Field(..., max_length=100)
    filed_date: datetime
    filing_number: str = Field(..., max_length=255)
    status: str = Field(..., max_length=50)
    details: Optional[str] = None
    risk_level: RiskLevelEnum
    source: str = Field(..., max_length=100)
    document_url: Optional[HttpUrl] = None


class LegalFilingCreate(LegalFilingBase):
    entity_id: int
    filing_data: Optional[Dict] = None


class LegalFilingResponse(LegalFilingBase):
    id: int
    entity_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class LegalRiskBase(BaseModel):
    risk_type: str = Field(..., max_length=100)
    description: Optional[str] = None
    severity: RiskLevelEnum
    count: int = Field(0, ge=0)
    status: str = Field(..., max_length=50)


class LegalRiskCreate(LegalRiskBase):
    entity_id: int
    details: Optional[Dict] = None


class LegalRiskResponse(LegalRiskBase):
    id: int
    entity_id: int
    detection_date: datetime
    update_date: datetime
    
    class Config:
        from_attributes = True


class LegalRiskDetectionRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    cin: Optional[str] = None
    gst_number: Optional[str] = None


class LegalRiskDetectionResponse(BaseModel):
    company_name: str
    compliance_status: ComplianceStatusEnum
    risk_level: RiskLevelEnum
    findings: List[Dict]  # Legal filings and risks
    risk_factors: List[str]
    recommendations: List[str]
    analysis_date: datetime


# Market Sentiment Schema
class SocialSentimentMetrics(BaseModel):
    source: str
    positive_mentions: int = 0
    negative_mentions: int = 0
    neutral_mentions: int = 0
    sentiment_score: float = Field(..., ge=-1, le=1)
    trending: bool
    trend_direction: Optional[str] = None
    sample_keywords: List[str]
    collected_at: datetime


class AnalystSentimentMetrics(BaseModel):
    source: str
    analyst_rating: Optional[str] = None
    average_target_price: Optional[float] = None
    current_price: Optional[float] = None
    upside_potential: Optional[float] = None
    number_of_analysts: int = 0
    bullish_count: int = 0
    neutral_count: int = 0
    bearish_count: int = 0
    consensus: Optional[str] = None
    analyst_sentiment_score: float = Field(..., ge=-1, le=1)
    industry_outlook: Optional[str] = None


class CompetitivePosition(BaseModel):
    market_share: Optional[float] = None
    rank_in_industry: Optional[int] = None
    competitor_comparison: Optional[Dict[str, str]] = None
    growth_vs_peers: Optional[float] = None
    market_perception: Optional[str] = None
    brand_strength: Optional[float] = Field(None, ge=0, le=1)


class MarketSentimentAnalysisRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    industry: Optional[str] = None


class MarketSentimentAnalysisResponse(BaseModel):
    company_name: str
    composite_sentiment_score: float = Field(..., ge=-1, le=1)
    market_tone: Dict
    social_sentiment: Optional[SocialSentimentMetrics] = None
    industry_sentiment: Optional[AnalystSentimentMetrics] = None
    competitive_position: Optional[CompetitivePosition] = None
    overall_assessment: str
    analysis_date: datetime


# Industry Report Schema
class IndustryReportBase(BaseModel):
    industry: str = Field(..., max_length=255)
    report_type: str = Field(..., max_length=100)
    market_size: Optional[float] = None
    market_size_currency: str = Field('INR', max_length=10)
    growth_rate_cagr: Optional[float] = None
    market_concentration: Optional[str] = None
    analyst_consensus: Optional[str] = None
    market_attractiveness: Optional[str] = None
    regulatory_environment: Optional[str] = None
    economic_health_score: Optional[float] = Field(None, ge=0, le=100)


class IndustryReportCreate(IndustryReportBase):
    entity_id: int
    market_drivers: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    key_players: Optional[List[str]] = None
    report_data: Optional[Dict] = None


class IndustryReportResponse(IndustryReportBase):
    id: int
    entity_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IndustryIntelligenceRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    industry: Optional[str] = None


class IndustryIntelligenceResponse(BaseModel):
    company_name: str
    industry: Optional[str]
    reports: List[Dict]
    market_attractiveness: str
    growth_opportunities: List[str]
    risks: List[str]
    collected_at: datetime


# Research Report Schema
class ResearchReportSummary(BaseModel):
    key_findings: List[str]
    news_highlights: int
    legal_status: str
    market_sentiment: str
    industry_outlook: str


class OverallAssessment(BaseModel):
    overall_rating: str
    reliability_score: float = Field(..., ge=0, le=1)
    key_strengths: List[str]
    key_weaknesses: List[str]
    critical_issues: List[str]
    recommendations: List[str]


class ComprehensiveResearchRequest(BaseModel):
    entity_id: Optional[int] = None
    company_name: str = Field(..., min_length=1)
    cin: Optional[str] = None
    gst_number: Optional[str] = None
    industry: Optional[str] = None
    include_news: bool = True
    include_legal: bool = True
    include_sentiment: bool = True
    include_industry: bool = True


class ComprehensiveResearchResponse(BaseModel):
    company_name: str
    report_type: str
    generated_at: datetime
    sections: Dict  # news, legal, sentiment, industry sections
    executive_summary: Optional[ResearchReportSummary] = None
    overall_assessment: Optional[OverallAssessment] = None


class ResearchReportBase(BaseModel):
    report_type: str = Field('COMPREHENSIVE', max_length=100)
    news_articles_count: int = 0
    legal_filings_count: int = 0
    risk_factors_count: int = 0
    sentiment_data_points: int = 0
    industry_reports_count: int = 0
    overall_rating: str
    reliability_score: float = Field(..., ge=0, le=1)
    confidence_level: float = Field(..., ge=0, le=1)


class ResearchReportCreate(ResearchReportBase):
    entity_id: int
    executive_summary: Optional[Dict] = None
    key_findings: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None
    key_risks: Optional[List[str]] = None
    critical_issues: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    monitoring_params: Optional[List[str]] = None


class ResearchReportResponse(ResearchReportBase):
    id: int
    entity_id: int
    key_findings: List[str]
    strengths: List[str]
    weaknesses: List[str]
    risks: List[str]
    opportunities: List[str]
    key_risks: List[str]
    critical_issues: List[str]
    recommendations: List[str]
    is_complete: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Research Task Schema
class ResearchTaskCreate(BaseModel):
    entity_id: int
    task_type: str = Field(..., max_length=100)
    search_depth: str = Field('STANDARD', max_length=50)
    parameters: Optional[Dict] = None


class ResearchTaskResponse(BaseModel):
    id: int
    entity_id: int
    task_type: str
    status: str
    progress_percentage: int = Field(..., ge=0, le=100)
    results: Optional[Dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[float] = None
    
    class Config:
        from_attributes = True


class ResearchTaskUpdate(BaseModel):
    status: Optional[str] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    results: Optional[Dict] = None
    error_message: Optional[str] = None


# Bulk Operations
class BulkResearchRequest(BaseModel):
    company_names: List[str] = Field(..., min_items=1, max_items=100)
    research_type: str = Field('COMPREHENSIVE', max_length=100)
    include_news: bool = True
    include_legal: bool = True
    include_sentiment: bool = True
    include_industry: bool = True


class BulkResearchResponse(BaseModel):
    total_companies: int
    completed: int
    failed: int
    in_progress: int
    created_tasks: List[int]  # Task IDs for tracking
    created_at: datetime
