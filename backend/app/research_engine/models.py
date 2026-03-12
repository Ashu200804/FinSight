"""
Research Engine Database Models

Stores research data, filings, sentiment, and intelligence
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.config import Base


class CompanyNews(Base):
    """News articles and press releases for companies"""
    
    __tablename__ = "company_news"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    title = Column(String(500), nullable=False)
    source = Column(String(255), nullable=False)
    published_at = Column(DateTime, nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    description = Column(Text)
    content = Column(Text)
    image_url = Column(String(1000))
    sentiment = Column(String(50))  # POSITIVE, NEGATIVE, NEUTRAL
    sentiment_score = Column(Float)  # -1 to 1
    news_type = Column(String(50))  # GENERAL_NEWS, FINANCIAL_NEWS, NEWS_AGGREGATOR
    relevance_score = Column(Float)  # 0 to 1
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entity = relationship("Entity", backref="news_articles")


class LegalFiling(Base):
    """Legal filings, regulatory documents, and compliance records"""
    
    __tablename__ = "legal_filings"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    filing_type = Column(String(100), nullable=False)  # ANNUAL_RETURN, DISCLOSURE, etc.
    filed_date = Column(DateTime, nullable=False)
    filing_number = Column(String(255), unique=True, nullable=False)
    status = Column(String(50))  # COMPLIANT, FILED, PENDING, VIOLATION
    details = Column(Text)
    risk_level = Column(String(50))  # LOW, MEDIUM, HIGH, CRITICAL
    source = Column(String(100))  # MCA, BSE, NSE, etc.
    document_url = Column(String(1000))
    filing_data = Column(JSON)  # Structured filing data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    entity = relationship("Entity", backref="legal_filings")


class LegalRisk(Base):
    """Detected legal and regulatory risks"""
    
    __tablename__ = "legal_risks"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    risk_type = Column(String(100), nullable=False)  # LITIGATION, VIOLATION, COMPLIANCE
    description = Column(Text)
    severity = Column(String(50))  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    count = Column(Integer, default=0)  # Number of incidents
    status = Column(String(50))  # CLEAR, UNDER_INVESTIGATION, RESOLVED
    detection_date = Column(DateTime, default=datetime.utcnow)
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    details = Column(JSON)  # Additional risk details
    
    # Relationships
    entity = relationship("Entity", backref="legal_risks")


class MarketSentiment(Base):
    """Market sentiment and perception analysis"""
    
    __tablename__ = "market_sentiment"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    
    # Social sentiment metrics
    positive_mentions = Column(Integer, default=0)
    negative_mentions = Column(Integer, default=0)
    neutral_mentions = Column(Integer, default=0)
    social_sentiment_score = Column(Float)  # -1 to 1
    social_trending = Column(Boolean, default=False)
    social_trend_direction = Column(String(50))  # POSITIVE, NEGATIVE, STABLE
    
    # Industry analyst sentiment
    analyst_rating = Column(String(50))  # BUY, HOLD, SELL
    average_target_price = Column(Float)
    analyst_sentiment_score = Column(Float)  # -1 to 1
    bullish_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    bearish_count = Column(Integer, default=0)
    
    # Competitive position
    market_share = Column(Float)  # percentage
    rank_in_industry = Column(Integer)
    brand_strength_score = Column(Float)  # 0 to 1
    
    # Composite
    composite_sentiment_score = Column(Float)  # -1 to 1
    overall_tone = Column(String(50))  # VERY_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sentiment_data = Column(JSON)  # Raw sentiment data
    
    # Relationships
    entity = relationship("Entity", backref="market_sentiments")


class IndustryReport(Base):
    """Industry reports and market intelligence"""
    
    __tablename__ = "industry_reports"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    industry = Column(String(255), nullable=False)
    report_type = Column(String(100), nullable=False)  # INDUSTRY_OVERVIEW, MARKET_SIZE, ECONOMIC_INDICATORS, REGULATORY_TRENDS
    
    # Market data
    market_size = Column(Float)  # in million INR
    market_size_currency = Column(String(10), default='INR')
    growth_rate_cagr = Column(Float)  # compound annual growth rate
    growth_period = Column(String(50))
    
    # Market concentration
    market_concentration = Column(String(50))  # LOW, MODERATE, HIGH, VERY_HIGH
    
    # Key players
    key_players = Column(JSON)  # List of competitors with market share
    
    # Drivers and challenges
    market_drivers = Column(JSON)  # List of positive factors
    challenges = Column(JSON)  # List of challenges
    
    # Analyst consensus
    analyst_consensus = Column(String(50))  # BULLISH, NEUTRAL, BEARISH
    market_attractiveness = Column(String(50))  # VERY_ATTRACTIVE, ATTRACTIVE, MODERATELY_ATTRACTIVE, LESS_ATTRACTIVE
    
    # Regulatory and economic
    regulatory_environment = Column(String(50))  # FAVORABLE, NEUTRAL, UNFAVORABLE
    economic_health_score = Column(Float)  # 0 to 100
    
    report_data = Column(JSON)  # Full report data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entity = relationship("Entity", backref="industry_reports")


class ResearchReport(Base):
    """Comprehensive research reports"""
    
    __tablename__ = "research_reports"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    report_type = Column(String(100), default='COMPREHENSIVE')
    
    # Report components (counts of included data)
    news_articles_count = Column(Integer, default=0)
    legal_filings_count = Column(Integer, default=0)
    risk_factors_count = Column(Integer, default=0)
    sentiment_data_points = Column(Integer, default=0)
    industry_reports_count = Column(Integer, default=0)
    
    # Key findings
    executive_summary = Column(JSON)
    key_findings = Column(JSON)  # List of key findings
    strengths = Column(JSON)  # List of strengths
    weaknesses = Column(JSON)  # List of weaknesses
    risks = Column(JSON)  # List of risks
    opportunities = Column(JSON)  # List of opportunities
    
    # Overall assessment
    overall_rating = Column(String(50))  # EXCELLENT, GOOD, FAIR, POOR, CRITICAL
    reliability_score = Column(Float)  # 0 to 1
    confidence_level = Column(Float)  # 0 to 1 (based on data completeness)
    
    # Risk assessment
    key_risks = Column(JSON)  # Top identified risks
    critical_issues = Column(JSON)  # Critical issues requiring immediate attention
    
    # Recommendations
    recommendations = Column(JSON)  # List of recommendations
    monitoring_params = Column(JSON)  # Parameters to monitor
    
    # Report status
    is_complete = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    reviewed_by = Column(Integer, ForeignKey("users.id"))  # Analyst who reviewed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entity = relationship("Entity", backref="research_reports")
    reviewer = relationship("User", backref="reviewed_research_reports")


class ResearchTask(Base):
    """Tracks research tasks and collection jobs"""
    
    __tablename__ = "research_tasks"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    task_type = Column(String(100), nullable=False)  # NEWS_SEARCH, LEGAL_CHECK, SENTIMENT_ANALYSIS, INDUSTRY_INTEL
    
    # Task parameters
    search_depth = Column(String(50), default='STANDARD')  # QUICK, STANDARD, COMPREHENSIVE
    parameters = Column(JSON)  # Task-specific parameters
    
    # Progress tracking
    status = Column(String(50), default='PENDING')  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    progress_percentage = Column(Integer, default=0)  # 0-100
    
    # Results
    results = Column(JSON)  # Task results
    error_message = Column(Text)  # Error details if failed
    
    # Metadata
    requested_by = Column(Integer, ForeignKey("users.id"))  # User who requested
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    execution_time_seconds = Column(Float)  # Time taken to complete
    
    # Relationships
    entity = relationship("Entity", backref="research_tasks")
    requester = relationship("User", backref="research_tasks")
