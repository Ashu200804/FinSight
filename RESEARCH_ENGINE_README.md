# Research Engine Module (Module 9)

## Overview

The Research Engine is a comprehensive intelligence-gathering system that aggregates data from multiple sources to provide deep insights into companies. It combines news analysis, legal risk detection, market sentiment analysis, and industry intelligence into a single unified platform.

**Status:** ✅ PRODUCTION READY

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Research Engine                          │
│              (Orchestration & Coordination)                 │
└──────┬──────────┬──────────┬──────────┬──────────────────────┘
       │          │          │          │
       v          v          v          v
┌──────────────┬──────────────┬──────────────┬──────────────┐
│News Article  │Legal         │Market        │Industry      │
│Collector     │Filings       │Sentiment     │Reports       │
│              │Analyzer      │Analyzer      │Gatherer      │
│- NewsAPI     │- MCA Files   │- Social      │- Market Data │
│- GNews       │- Stock Exch  │- Analysts    │- Regulations │
│- Web Scrape  │- Litigation  │- Sentiment   │- Economic    │
└──────────────┴──────────────┴──────────────┴──────────────┘
       │          │          │          │
       └──────────┴──────────┴──────────┴──────────────────────┐
                                                               │
                            ┌──────────────────────────────────┘
                            │
                            v
                    ┌────────────────┐
                    │  Research      │
                    │  Aggregator    │
                    │                │
                    │ - Compiling    │
                    │ - Analysis     │
                    │ - Scoring      │
                    │ - Reporting    │
                    └────────┬───────┘
                             │
              ┌──────────────┴──────────────┐
              v                             v
    ┌──────────────────────┐    ┌──────────────────────┐
    │   Database Storage   │    │  Frontend Display    │
    │                      │    │                      │
    │ - News Articles      │    │ - Research Dashboard │
    │ - Legal Filings      │    │ - News Viewer        │
    │ - Sentiment Data     │    │ - Risk Analysis      │
    │ - Reports            │    │ - Sentiment Charts   │
    │ - Tasks              │    │ - Industry Reports   │
    └──────────────────────┘    └──────────────────────┘
```

## Data Sources

### 1. News Articles Collector
**Sources:**
- NewsAPI (newsapi.org)
- GNews API (gnews.io)
- Web scraping: Moneycontrol, Economic Times, etc.

**Features:**
- Automatic sentiment classification (positive/neutral/negative)
- Date filtering and trending detection
- Source verification
- Relevance scoring

### 2. Legal Filings Analyzer
**Sources:**
- MCA (Ministry of Corporate Affairs) filings
- Stock Exchange Filings (BSE, NSE)
- Court records and litigation data
- Regulatory violation databases

**Risk Types Detected:**
- LITIGATION - Active court cases
- REGULATORY_VIOLATIONS - Non-compliance issues
- TAX_COMPLIANCE - Tax filing status
- REGULATORY_ENVIRONMENT - Sector-specific regulations

### 3. Market Sentiment Analyzer
**Sources:**
- Social media mentions (Twitter/X, LinkedIn)
- Analyst reports and ratings
- Competitor positioning analysis
- Brand strength metrics

**Metrics:**
- Sentiment score (-1 to +1)
- Mention counts (positive/negative/neutral)
- Analyst consensus (BUY/HOLD/SELL)
- Market share and competitive ranking

### 4. Industry Reports Gatherer
**Sources:**
- Industry publications and reports
- Market research databases
- Government economic data
- Regulatory trend analysis

**Intelligence:**
- Market size and growth rates
- Segment information
- Key market drivers and challenges
- Regulatory environment
- Economic indicators

## Core Functions

### 1. search_company_news()

```python
async def search_company_news(
    company_name: str,
    days_back: int = 30,
    sentiment_filter: str = None,
    limit: int = 50
) -> Dict
```

**Purpose:** Search and aggregate news articles about a company

**Returns:**
```json
{
  "company_name": "ABC Corp",
  "total_articles_found": 45,
  "articles": [
    {
      "title": "ABC Corp Expands Operations",
      "source": "Reuters",
      "published_at": "2024-01-15T10:30:00Z",
      "url": "https://...",
      "sentiment": "POSITIVE",
      "news_type": "GENERAL_NEWS"
    }
  ],
  "sentiment_breakdown": {
    "POSITIVE": 60,
    "NEUTRAL": 25,
    "NEGATIVE": 15
  },
  "trend": "POSITIVE",
  "trending_topics": ["expansion", "growth", "investment"]
}
```

### 2. detect_legal_risks()

```python
async def detect_legal_risks(
    company_name: str,
    cin: str = None,
    gst_number: str = None
) -> Dict
```

**Purpose:** Identify legal, regulatory, and compliance risks

**Returns:**
```json
{
  "company_name": "ABC Corp",
  "compliance_status": "COMPLIANT",
  "risk_level": "LOW",
  "findings": [
    {
      "filing_type": "ANNUAL_RETURN",
      "filed_date": "2024-01-10T00:00:00Z",
      "status": "COMPLIANT",
      "risk_level": "LOW"
    }
  ],
  "risk_factors": [],
  "recommendations": ["Continue monitoring", "Maintain compliance"]
}
```

### 3. analyze_market_sentiment()

```python
async def analyze_market_sentiment(
    company_name: str,
    industry: str = None
) -> Dict
```

**Purpose:** Analyze market perception and social sentiment

**Returns:**
```json
{
  "company_name": "ABC Corp",
  "composite_sentiment_score": 0.73,
  "overall_assessment": "GOOD",
  "market_tone": {
    "overall_tone": "POSITIVE",
    "confidence": 0.78,
    "momentum": "BUILDING"
  },
  "social_sentiment": {
    "positive_mentions": 456,
    "negative_mentions": 32,
    "sentiment_score": 0.78
  },
  "industry_sentiment": {
    "analyst_rating": "BUY",
    "bullish_count": 9,
    "neutral_count": 2,
    "bearish_count": 1
  },
  "competitive_position": {
    "market_share": 15.5,
    "rank_in_industry": 3,
    "brand_strength": 0.82
  }
}
```

### 4. gather_industry_intelligence()

```python
async def gather_industry_intelligence(
    company_name: str,
    industry: str = None
) -> Dict
```

**Purpose:** Collect and analyze industry data

**Returns:**
```json
{
  "industry": "MANUFACTURING",
  "market_attractiveness": "ATTRACTIVE",
  "reports": [
    {
      "report_type": "INDUSTRY_OVERVIEW",
      "market_size": 500000,
      "growth_rate_cagr": 12.5,
      "key_players": ["Company A", "Company B"],
      "market_drivers": ["Growth", "Innovation"],
      "challenges": ["Rising costs", "Supply chain"]
    }
  ],
  "growth_opportunities": [...],
  "risks": [...]
}
```

### 5. generate_comprehensive_research_report()

**Purpose:** Combine all sources into a comprehensive report

**Sections:**
- Executive Summary
- News Analysis with Sentiment
- Legal Risk Assessment
- Market Sentiment Analysis
- Industry Intelligence
- Overall Assessment with Recommendations

## Database Models

### CompanyNews
```sql
CREATE TABLE company_news (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER REFERENCES entities(id),
  title VARCHAR(500),
  source VARCHAR(255),
  published_at TIMESTAMP,
  url VARCHAR(1000),
  description TEXT,
  sentiment VARCHAR(50),
  sentiment_score FLOAT,
  news_type VARCHAR(50),
  relevance_score FLOAT,
  created_at TIMESTAMP
);
```

### LegalFiling
```sql
CREATE TABLE legal_filings (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER REFERENCES entities(id),
  filing_type VARCHAR(100),
  filed_date TIMESTAMP,
  filing_number VARCHAR(255),
  status VARCHAR(50),
  risk_level VARCHAR(50),
  source VARCHAR(100),
  created_at TIMESTAMP
);
```

### LegalRisk
```sql
CREATE TABLE legal_risks (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER REFERENCES entities(id),
  risk_type VARCHAR(100),
  severity VARCHAR(50),
  count INTEGER,
  status VARCHAR(50),
  detection_date TIMESTAMP
);
```

### MarketSentiment
```sql
CREATE TABLE market_sentiment (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER REFERENCES entities(id),
  analysis_date TIMESTAMP,
  positive_mentions INTEGER,
  negative_mentions INTEGER,
  neutral_mentions INTEGER,
  social_sentiment_score FLOAT,
  composite_sentiment_score FLOAT,
  overall_tone VARCHAR(50),
  analyst_rating VARCHAR(50),
  market_share FLOAT,
  brand_strength_score FLOAT
);
```

### IndustryReport
```sql
CREATE TABLE industry_reports (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER REFERENCES entities(id),
  industry VARCHAR(255),
  report_type VARCHAR(100),
  market_size FLOAT,
  growth_rate_cagr FLOAT,
  market_concentration VARCHAR(50),
  market_attractiveness VARCHAR(50)
);
```

### ResearchReport
```sql
CREATE TABLE research_reports (
  id INTEGER PRIMARY KEY,
  entity_id INTEGER REFERENCES entities(id),
  report_type VARCHAR(100),
  overall_rating VARCHAR(50),
  reliability_score FLOAT,
  key_findings JSON,
  strengths JSON,
  weaknesses JSON,
  risks JSON,
  recommendations JSON,
  created_at TIMESTAMP
);
```

## API Endpoints

### News Search
```
POST /api/research/news/search
```

**Request:**
```json
{
  "company_name": "ABC Corporation",
  "days_back": 30,
  "sentiment_filter": "POSITIVE",
  "limit": 50
}
```

### Legal Risk Detection
```
POST /api/research/legal/detect-risks
```

**Request:**
```json
{
  "company_name": "ABC Corporation",
  "cin": "U12345AB2020PLC123456",
  "gst_number": "22AABCT1234H1Z0"
}
```

### Market Sentiment Analysis
```
POST /api/research/sentiment/analyze
```

**Request:**
```json
{
  "company_name": "ABC Corporation",
  "industry": "MANUFACTURING"
}
```

### Industry Intelligence
```
POST /api/research/industry/intelligence
```

**Request:**
```json
{
  "company_name": "ABC Corporation",
  "industry": "MANUFACTURING"
}
```

### Comprehensive Research Report
```
POST /api/research/comprehensive
```

**Request:**
```json
{
  "company_name": "ABC Corporation",
  "cin": "U12345AB2020PLC123456",
  "gst_number": "22AABCT1234H1Z0",
  "industry": "MANUFACTURING",
  "include_news": true,
  "include_legal": true,
  "include_sentiment": true,
  "include_industry": true
}
```

### Get Entity Research Report
```
GET /api/research/entity/{entity_id}/latest-report
```

### Get Entity News
```
GET /api/research/entity/{entity_id}/news?days=30&limit=20
```

### Get Entity Legal Risks
```
GET /api/research/entity/{entity_id}/legal-risks
```

### Get Entity Sentiment
```
GET /api/research/entity/{entity_id}/sentiment
```

### Create Research Task
```
POST /api/research/tasks
```

**Request:**
```json
{
  "entity_id": 123,
  "task_type": "COMPREHENSIVE_RESEARCH",
  "search_depth": "COMPREHENSIVE",
  "parameters": {}
}
```

### Get Research Task Status
```
GET /api/research/tasks/{task_id}
```

### Create Bulk Research
```
POST /api/research/bulk
```

**Request:**
```json
{
  "company_names": ["ABC Corp", "XYZ Ltd", "PQR Inc"],
  "research_type": "COMPREHENSIVE",
  "include_news": true,
  "include_legal": true
}
```

## Frontend Components

### ResearchDashboard
Main research interface with tabs for different data sources.

**Props:**
- `entityId` (number) - Entity to research
- `entityName` (string) - Company name
- `onClose` (function) - Callback when closing

**Tabs:**
1. **Overview** - Executive summary and key findings
2. **News** - Articles with sentiment filtering
3. **Legal** - Risk detection and compliance status
4. **Sentiment** - Market perception and analyst ratings
5. **Industry** - Industry reports and market intelligence

**Features:**
- Generate comprehensive research report
- Filter news by sentiment
- View legal risk severity levels
- Compare analyst ratings
- Track market attractiveness

## Usage Examples

### Backend Usage

```python
from app.research_engine import ResearchEngine

engine = ResearchEngine(
    newsapi_key='your_newsapi_key',
    gnews_key='your_gnews_key'
)

# Search news
news = await engine.search_company_news('Apple Inc', days_back=30)

# Detect legal risks
risks = await engine.detect_legal_risks('Apple Inc', cin='U63090CA1976PLC006785')

# Analyze sentiment
sentiment = await engine.analyze_market_sentiment('Apple Inc', industry='TECHNOLOGY')

# Gather industry intelligence
intelligence = await engine.gather_industry_intelligence('Apple Inc', industry='TECHNOLOGY')

# Generate comprehensive report
report = await engine.generate_comprehensive_research_report(
    company_name='Apple Inc',
    cin='U63090CA1976PLC006785',
    industry='TECHNOLOGY'
)
```

### Frontend Usage

```jsx
import { ResearchDashboard } from '@/components/ResearchDashboard';
import { researchService } from '@/services/researchService';

// In a page component
export function CompanyResearchPage({ entityId, entityName }) {
  return (
    <ResearchDashboard
      entityId={entityId}
      entityName={entityName}
      onClose={() => navigate(-1)}
    />
  );
}

// Or use individual functions
const news = await researchService.searchCompanyNews({
  company_name: 'ABC Corp',
  days_back: 30,
  limit: 50
});

const risks = await researchService.detectLegalRisks({
  company_name: 'ABC Corp',
  cin: 'U12345AB2020PLC123456'
});

const sentiment = await researchService.analyzeMarketSentiment({
  company_name: 'ABC Corp',
  industry: 'MANUFACTURING'
});
```

## Integration with Credit Scoring

The Research Engine enhances credit scoring by providing external validation:

1. **Risk Assessment** - Legal findings feed into credit risk model
2. **Market Sentiment** - Public perception influences default probability
3. **Industry Health** - Sector trends affect company rating
4. **News Impact** - Recent articles can trigger score updates

## Performance Considerations

### Caching Strategy
```python
# Cache news for 6 hours
# Cache legal filings for 24 hours
# Cache sentiment for 12 hours
# Cache industry data for 30 days
```

### Async Operations
- All external API calls run asynchronously
- Concurrent data gathering from multiple sources
- Background task processing for bulk operations

### Database Optimization
```sql
CREATE INDEX idx_news_entity_date ON company_news(entity_id, published_at);
CREATE INDEX idx_legal_entity_severity ON legal_filings(entity_id, risk_level);
CREATE INDEX idx_sentiment_entity_date ON market_sentiment(entity_id, analysis_date);
```

## Error Handling

**Common Issues:**
1. API rate limits - Implement throttling and backoff
2. Data unavailability - Return partial results with flags
3. Parsing errors - Log and skip problematic sources
4. Timeout issues - Set timeouts and provide fallbacks

## Future Enhancements

- [ ] Real-time news feed with push notifications
- [ ] Machine learning for anomaly detection
- [ ] Supply chain risk analysis
- [ ] ESG (Environmental, Social, Governance) scoring
- [ ] Peer benchmarking and comparative analysis
- [ ] Automated research report generation with templates
- [ ] Integration with credit rating agencies
- [ ] Geopolitical risk assessment

## Configuration

### Environment Variables

```env
# News API Keys
NEWSAPI_KEY=your_newsapi_key
GNEWS_KEY=your_gnews_key

# MCA API
MCA_API_KEY=your_mca_api_key

# Web Scraping Config
SCRAPER_TIMEOUT=10
SCRAPER_RETRY_COUNT=3
SCRAPER_USER_AGENT=Mozilla/5.0...

# Sentiment Analysis
SENTIMENT_MODEL=textblob  # or transformers

# Cache Settings
NEWS_CACHE_TTL=21600  # 6 hours
LEGAL_CACHE_TTL=86400  # 24 hours
SENTIMENT_CACHE_TTL=43200  # 12 hours
INDUSTRY_CACHE_TTL=2592000  # 30 days
```

## Dependencies

**Backend:**
- `aiohttp` - Async HTTP requests
- `requests` - Synchronous HTTP
- `beautifulsoup4` - Web scraping
- `textblob` - Sentiment analysis

**Install:**
```bash
pip install aiohttp requests beautifulsoup4 textblob
```

## Support & Maintenance

For API keys and integrations:
1. NewsAPI: https://newsapi.org
2. GNews: https://gnews.io
3. MCA: https://www.mca.gov.in

## File Inventory

**Backend (1500+ lines):**
- `research_engine.py` - Core engine with 4 collectors
- `models.py` - 7 database models
- `schemas.py` - Pydantic validation
- `routes.py` - 10 API endpoints
- `__init__.py` - Module exports

**Frontend (1000+ lines):**
- `ResearchDashboard.jsx` - Main interface
- `researchService.js` - Service layer

---

**Module 9 Status:** ✅ PRODUCTION READY
**Last Updated:** January 2024
**Version:** 1.0
