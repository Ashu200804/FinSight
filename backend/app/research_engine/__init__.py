"""
Research Engine Module Initialization

Exports research engine components and utilities
"""

from app.research_engine.research_engine import (
    ResearchEngine,
    NewsArticleCollector,
    LegalFilingsAnalyzer,
    MarketSentimentAnalyzer,
    IndustryReportsGatherer
)

from app.research_engine.models import (
    CompanyNews,
    LegalFiling,
    LegalRisk,
    MarketSentiment,
    IndustryReport,
    ResearchReport,
    ResearchTask
)

__all__ = [
    'ResearchEngine',
    'NewsArticleCollector',
    'LegalFilingsAnalyzer',
    'MarketSentimentAnalyzer',
    'IndustryReportsGatherer',
    'CompanyNews',
    'LegalFiling',
    'LegalRisk',
    'MarketSentiment',
    'IndustryReport',
    'ResearchReport',
    'ResearchTask'
]
