"""
Research Engine API Routes

Endpoints for research operations and intelligence gathering
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
import logging
import os

from app.database.config import get_db
from app.auth.routes import get_current_user
from app.models.user import User
from app.models.entity import Entity
from app.research_engine.research_engine import ResearchEngine
from app.research_engine.models import (
    CompanyNews, LegalFiling, LegalRisk, MarketSentiment, 
    IndustryReport, ResearchReport, ResearchTask
)
from app.research_engine.schemas import (
    NewsSearchRequest, NewsSearchResponse,
    LegalRiskDetectionRequest, LegalRiskDetectionResponse,
    MarketSentimentAnalysisRequest, MarketSentimentAnalysisResponse,
    IndustryIntelligenceRequest, IndustryIntelligenceResponse,
    ComprehensiveResearchRequest, ComprehensiveResearchResponse,
    ResearchTaskResponse, ResearchTaskCreate, BulkResearchRequest, BulkResearchResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["Research & Intelligence"])

# Initialize research engine with API keys (from environment)
research_engine = ResearchEngine(
    newsapi_key=os.getenv('NEWSAPI_KEY'),
    gnews_key=os.getenv('GNEWS_KEY'),
    mca_api_key=os.getenv('MCA_API_KEY')
)


@router.post("/news/search", response_model=NewsSearchResponse)
async def search_company_news(
    request: NewsSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search for news articles about a company
    
    Args:
        company_name: Company name to search
        days_back: Number of days to look back (1-365)
        sentiment_filter: Filter by sentiment (POSITIVE, NEGATIVE, NEUTRAL)
        limit: Max articles to return (1-200)
    
    Returns:
        News articles with sentiment breakdown and trends
    """
    try:
        # Run async search
        result = await research_engine.search_company_news(
            company_name=request.company_name,
            days_back=request.days_back,
            sentiment_filter=request.sentiment_filter,
            limit=request.limit
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
    
    except Exception as e:
        logger.error(f"Error searching news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"News search failed: {str(e)}")


@router.post("/legal/detect-risks", response_model=LegalRiskDetectionResponse)
async def detect_legal_risks(
    request: LegalRiskDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detect legal and regulatory risks for a company
    
    Args:
        company_name: Company name
        cin: Corporate Identification Number (optional)
        gst_number: GST Number (optional)
    
    Returns:
        Legal filings, risks, and compliance status
    """
    try:
        result = await research_engine.detect_legal_risks(
            company_name=request.company_name,
            cin=request.cin,
            gst_number=request.gst_number
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
    
    except Exception as e:
        logger.error(f"Error detecting legal risks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Legal risk detection failed: {str(e)}")


@router.post("/sentiment/analyze", response_model=MarketSentimentAnalysisResponse)
async def analyze_market_sentiment(
    request: MarketSentimentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze market sentiment and perception of company
    
    Args:
        company_name: Company name
        industry: Industry classification (optional)
    
    Returns:
        Sentiment scores from social media, analysts, and competitive analysis
    """
    try:
        result = await research_engine.analyze_market_sentiment(
            company_name=request.company_name,
            industry=request.industry
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


@router.post("/industry/intelligence", response_model=IndustryIntelligenceResponse)
async def gather_industry_intelligence(
    request: IndustryIntelligenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gather industry intelligence and market reports
    
    Args:
        company_name: Company name
        industry: Industry classification (optional)
    
    Returns:
        Industry overview, market size, growth rates, and trends
    """
    try:
        result = await research_engine.gather_industry_intelligence(
            company_name=request.company_name,
            industry=request.industry
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return result
    
    except Exception as e:
        logger.error(f"Error gathering industry intelligence: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Industry intelligence gathering failed: {str(e)}")


@router.post("/comprehensive", response_model=ComprehensiveResearchResponse)
async def generate_comprehensive_research(
    request: ComprehensiveResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate comprehensive research report
    
    Combines news, legal filings, market sentiment, and industry intelligence
    
    Args:
        company_name: Company name
        cin: CIN (optional)
        gst_number: GST Number (optional)
        industry: Industry classification (optional)
        include_news: Include news search (default true)
        include_legal: Include legal risk detection (default true)
        include_sentiment: Include sentiment analysis (default true)
        include_industry: Include industry intelligence (default true)
    
    Returns:
        Comprehensive research report with all sections
    """
    try:
        # Verify user role
        role_value = str(getattr(current_user, 'role', '')).lower()
        allowed_roles = {'analyst', 'credit_analyst', 'admin', 'userrole.analyst', 'userrole.credit_analyst', 'userrole.admin'}
        if role_value not in allowed_roles:
            raise HTTPException(status_code=403, detail="Unauthorized for research operations")
        
        entity = None
        if request.entity_id:
            entity = db.query(Entity).filter(Entity.id == request.entity_id).first()
            if not entity:
                raise HTTPException(status_code=404, detail="Entity not found")
        else:
            entity = db.query(Entity).filter(Entity.company_name.ilike(request.company_name)).first()

        result = await research_engine.generate_comprehensive_research_report(
            company_name=request.company_name,
            cin=request.cin,
            gst_number=request.gst_number,
            industry=request.industry,
            include_news=request.include_news,
            include_legal=request.include_legal,
            include_sentiment=request.include_sentiment,
            include_industry=request.include_industry
        )
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Optionally store report in database
        try:
            if entity:
                _persist_research_sections(db=db, entity_id=entity.id, result=result)

                db_report = ResearchReport(
                    entity_id=entity.id,
                    report_type='COMPREHENSIVE',
                    news_articles_count=len(result.get('sections', {}).get('news', {}).get('articles', [])),
                    legal_filings_count=len(result.get('sections', {}).get('legal', {}).get('findings', [])),
                    risk_factors_count=len(result.get('overall_assessment', {}).get('critical_issues', [])),
                    sentiment_data_points=1 if result.get('sections', {}).get('sentiment') else 0,
                    industry_reports_count=len(result.get('sections', {}).get('industry', {}).get('reports', [])),
                    overall_rating=result.get('overall_assessment', {}).get('overall_rating', 'UNKNOWN'),
                    reliability_score=float(result.get('overall_assessment', {}).get('reliability_score', 0) or 0),
                    confidence_level=0.8,
                    executive_summary=result.get('executive_summary', {}),
                    key_findings=result.get('executive_summary', {}).get('key_findings', []),
                    strengths=result.get('overall_assessment', {}).get('key_strengths', []),
                    weaknesses=result.get('overall_assessment', {}).get('key_weaknesses', []),
                    risks=result.get('overall_assessment', {}).get('critical_issues', []),
                    opportunities=[],
                    key_risks=result.get('overall_assessment', {}).get('critical_issues', []),
                    critical_issues=result.get('overall_assessment', {}).get('critical_issues', []),
                    recommendations=result.get('overall_assessment', {}).get('recommendations', []),
                    monitoring_params=[],
                    is_complete=True
                )
                db.add(db_report)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not store report: {str(e)}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating comprehensive research: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research generation failed: {str(e)}")


@router.post("/tasks", response_model=ResearchTaskResponse)
async def create_research_task(
    task_request: ResearchTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an async research task
    
    Args:
        entity_id: Entity to research
        task_type: NEWS_SEARCH, LEGAL_CHECK, SENTIMENT_ANALYSIS, INDUSTRY_INTEL
        search_depth: QUICK, STANDARD, COMPREHENSIVE
        parameters: Task-specific parameters
    
    Returns:
        Task details with ID for tracking
    """
    try:
        # Verify entity exists
        entity = db.query(Entity).filter(Entity.id == task_request.entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Create task
        task = ResearchTask(
            entity_id=task_request.entity_id,
            task_type=task_request.task_type,
            search_depth=task_request.search_depth,
            parameters=task_request.parameters,
            requested_by=current_user.id,
            status='PENDING'
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Schedule background execution
        background_tasks.add_task(
            execute_research_task,
            task_id=task.id,
            entity_id=entity.id,
            company_name=entity.company_name,
            task_type=task_request.task_type
        )
        
        return ResearchTaskResponse.from_orm(task)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating research task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


@router.get("/tasks/{task_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get research task status and results"""
    try:
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return ResearchTaskResponse.from_orm(task)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")


@router.get("/entity/{entity_id}/latest-report")
async def get_entity_latest_research_report(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get latest research report for entity"""
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        report = db.query(ResearchReport).filter(
            ResearchReport.entity_id == entity_id
        ).order_by(ResearchReport.created_at.desc()).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="No research report found for entity")
        
        return {
            'id': report.id,
            'report_type': report.report_type,
            'overall_rating': report.overall_rating,
            'reliability_score': report.reliability_score,
            'key_findings': report.key_findings,
            'strengths': report.strengths,
            'weaknesses': report.weaknesses,
            'risks': report.risks,
            'recommendations': report.recommendations,
            'created_at': report.created_at,
            'updated_at': report.updated_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")


@router.get("/entity/{entity_id}/news", response_model=list)
async def get_entity_news(
    entity_id: int,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get news articles for entity"""
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        recent_date = datetime.utcnow() - timedelta(days=days)
        
        news = db.query(CompanyNews).filter(
            CompanyNews.entity_id == entity_id,
            CompanyNews.published_at >= recent_date
        ).order_by(CompanyNews.published_at.desc()).limit(limit).all()
        
        return [
            {
                'id': n.id,
                'title': n.title,
                'source': n.source,
                'published_at': n.published_at,
                'url': n.url,
                'sentiment': n.sentiment,
                'sentiment_score': n.sentiment_score,
                'news_type': n.news_type
            }
            for n in news
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve news: {str(e)}")


@router.get("/entity/{entity_id}/legal-risks", response_model=list)
async def get_entity_legal_risks(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get legal risks for entity"""
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        risks = db.query(LegalRisk).filter(
            LegalRisk.entity_id == entity_id
        ).order_by(LegalRisk.severity.desc()).all()
        
        return [
            {
                'id': r.id,
                'risk_type': r.risk_type,
                'description': r.description,
                'severity': r.severity,
                'count': r.count,
                'status': r.status,
                'detection_date': r.detection_date
            }
            for r in risks
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve legal risks: {str(e)}")


@router.get("/entity/{entity_id}/sentiment", response_model=dict)
async def get_entity_market_sentiment(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get latest market sentiment for entity"""
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        sentiment = db.query(MarketSentiment).filter(
            MarketSentiment.entity_id == entity_id
        ).order_by(MarketSentiment.analysis_date.desc()).first()
        
        if not sentiment:
            raise HTTPException(status_code=404, detail="No sentiment data found")
        
        return {
            'id': sentiment.id,
            'analysis_date': sentiment.analysis_date,
            'composite_sentiment_score': sentiment.composite_sentiment_score,
            'overall_tone': sentiment.overall_tone,
            'positive_mentions': sentiment.positive_mentions,
            'negative_mentions': sentiment.negative_mentions,
            'neutral_mentions': sentiment.neutral_mentions,
            'social_sentiment_score': sentiment.social_sentiment_score,
            'analyst_rating': sentiment.analyst_rating,
            'analyst_sentiment_score': sentiment.analyst_sentiment_score,
            'market_share': sentiment.market_share,
            'brand_strength_score': sentiment.brand_strength_score
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sentiment: {str(e)}")


@router.post("/bulk", response_model=BulkResearchResponse)
async def create_bulk_research(
    request: BulkResearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create research tasks for multiple companies
    
    Args:
        company_names: List of company names (1-100)
        research_type: Type of research
        include_*: Include specific sections
    
    Returns:
        Created task IDs for tracking
    """
    try:
        if current_user.role not in ['ANALYST', 'ADMIN', 'CREDIT_ANALYST']:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        task_ids = []
        
        for company_name in request.company_names:
            task = ResearchTask(
                entity_id=0,  # Bulk research not tied to specific entity
                task_type='COMPREHENSIVE_RESEARCH',
                search_depth='STANDARD',
                parameters={'company_name': company_name},
                requested_by=current_user.id,
                status='PENDING'
            )
            db.add(task)
            db.flush()
            task_ids.append(task.id)
        
        db.commit()
        
        return BulkResearchResponse(
            total_companies=len(request.company_names),
            completed=0,
            failed=0,
            in_progress=0,
            created_tasks=task_ids,
            created_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bulk research: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk research creation failed: {str(e)}")


# Background task executor
async def execute_research_task(task_id: int, entity_id: int, company_name: str, task_type: str):
    """Execute research task in background"""
    # Implementation would run the actual research based on task type
    logger.info(f"Executing research task {task_id} for {company_name}")


def _safe_parse_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
        except Exception:
            return datetime.utcnow()
    return datetime.utcnow()


def _persist_research_sections(db: Session, entity_id: int, result: dict) -> None:
    sections = result.get('sections', {})

    news_section = sections.get('news', {}) or {}
    for article in news_section.get('articles', []) or []:
        url = article.get('url')
        if not url:
            continue
        existing = db.query(CompanyNews).filter(CompanyNews.url == str(url)).first()
        if existing:
            continue
        db.add(CompanyNews(
            entity_id=entity_id,
            title=article.get('title', 'Untitled'),
            source=article.get('source', 'Unknown'),
            published_at=_safe_parse_datetime(article.get('published_at')),
            url=str(url),
            description=article.get('description'),
            content=article.get('content'),
            image_url=article.get('image_url'),
            sentiment=article.get('sentiment', 'NEUTRAL'),
            sentiment_score=article.get('sentiment_score'),
            news_type=article.get('news_type', 'GENERAL_NEWS'),
            relevance_score=article.get('relevance_score')
        ))

    legal_section = sections.get('legal', {}) or {}
    for finding in legal_section.get('findings', []) or []:
        if finding.get('filing_type'):
            filing_number = finding.get('filing_number') or f"AUTO-{entity_id}-{finding.get('filing_type')}-{int(datetime.utcnow().timestamp())}"
            existing_filing = db.query(LegalFiling).filter(LegalFiling.filing_number == filing_number).first()
            if not existing_filing:
                db.add(LegalFiling(
                    entity_id=entity_id,
                    filing_type=finding.get('filing_type', 'UNKNOWN'),
                    filed_date=_safe_parse_datetime(finding.get('filed_date')),
                    filing_number=filing_number,
                    status=finding.get('status', 'UNKNOWN'),
                    details=finding.get('details'),
                    risk_level=finding.get('risk_level', 'LOW'),
                    source=finding.get('source', 'UNKNOWN')
                ))

        if finding.get('risk_type'):
            db.add(LegalRisk(
                entity_id=entity_id,
                risk_type=finding.get('risk_type', 'GENERAL'),
                description=finding.get('description'),
                severity=finding.get('severity', 'LOW'),
                count=int(finding.get('count', 0) or 0),
                status=finding.get('status', 'UNKNOWN'),
                details=finding
            ))

    sentiment = sections.get('sentiment', {}) or {}
    if sentiment:
        social = sentiment.get('social_sentiment', {}) or {}
        analyst = sentiment.get('industry_sentiment', {}) or {}
        competitive = sentiment.get('competitive_position', {}) or {}
        market_tone = sentiment.get('market_tone', {}) or {}

        db.add(MarketSentiment(
            entity_id=entity_id,
            analysis_date=_safe_parse_datetime(sentiment.get('analysis_date')),
            positive_mentions=int(social.get('positive_mentions', 0) or 0),
            negative_mentions=int(social.get('negative_mentions', 0) or 0),
            neutral_mentions=int(social.get('neutral_mentions', 0) or 0),
            social_sentiment_score=float(social.get('sentiment_score', 0) or 0),
            social_trending=bool(social.get('trending', False)),
            social_trend_direction=social.get('trend_direction'),
            analyst_rating=analyst.get('analyst_rating'),
            average_target_price=analyst.get('average_target_price'),
            analyst_sentiment_score=analyst.get('analyst_sentiment_score'),
            bullish_count=int(analyst.get('bullish_count', 0) or 0),
            neutral_count=int(analyst.get('neutral_count', 0) or 0),
            bearish_count=int(analyst.get('bearish_count', 0) or 0),
            market_share=competitive.get('market_share'),
            rank_in_industry=competitive.get('rank_in_industry'),
            brand_strength_score=competitive.get('brand_strength'),
            composite_sentiment_score=float(sentiment.get('composite_sentiment_score', 0) or 0),
            overall_tone=market_tone.get('overall_tone')
        ))

    industry_section = sections.get('industry', {}) or {}
    for report in industry_section.get('reports', []) or []:
        db.add(IndustryReport(
            entity_id=entity_id,
            industry=report.get('industry', 'UNKNOWN'),
            report_type=report.get('report_type', 'GENERAL'),
            market_size=report.get('market_size') or report.get('current_market_size'),
            market_size_currency=report.get('market_size_currency', 'INR'),
            growth_rate_cagr=report.get('growth_rate_cagr') or report.get('compound_annual_growth'),
            growth_period=report.get('growth_period'),
            market_concentration=report.get('market_concentration'),
            key_players=report.get('key_players'),
            market_drivers=report.get('market_drivers'),
            challenges=report.get('challenges'),
            analyst_consensus=report.get('consensus') or report.get('analyst_consensus'),
            market_attractiveness=industry_section.get('market_attractiveness') or report.get('market_attractiveness'),
            regulatory_environment=report.get('regulatory_environment'),
            economic_health_score=report.get('economic_health_score'),
            report_data=report
        ))

    db.commit()
