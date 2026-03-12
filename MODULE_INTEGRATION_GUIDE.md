# Module Integration Guide - Credit Scoring with Previous Modules

## System Architecture Overview

The credit scoring module integrates seamlessly with all previous modules to create a complete enterprise credit underwriting platform:

```
┌─────────────────────────────────────────────────────────────┐
│                    UNDERWRITING DASHBOARD                   │
│             (Credit Scoring & Recommendation)               │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴─────────────┬──────────────────┬────────────┐
    │                      │                  │            │
    v                      v                  v            v
┌─────────────┐   ┌──────────────────┐   ┌─────────┐  ┌──────────┐
│  Financial  │   │  Document        │   │ Entity  │  │ Bank     │
│  Metrics    │   │  Processing      │   │ Data    │  │ Relations│
│  Engine     │   │  (OCR, LLM)      │   │         │  │          │
│ (Module 7)  │   │ (Module 5-6)     │   │ (Mod 2) │  │ (Input)  │
└─────────────┘   └──────────────────┘   └─────────┘  └──────────┘
    │                      │                  │            │
    └────────────┬─────────┴──────────────────┴────────────┘
                 │
                 v
    ┌────────────────────────────────────┐
    │  Credit Scoring Engine (Module 8)  │
    │  - 8 Component Weighted Scoring    │
    │  - POD Calculation                 │
    │  - Risk Category Mapping           │
    └────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    v                         v
┌──────────────────┐  ┌──────────────────┐
│ Lending Decision │  │ Monitoring Plan  │
│ - Approve/Decline│  │ - KPI Tracking   │
│ - Interest Rate  │  │ - Alert System   │
│ - Conditions     │  │ - Covenant Mgmt  │
└──────────────────┘  └──────────────────┘
```

## Data Flow Through Modules

### 1. Entity Onboarding (Module 2) → Credit Scoring
```
Entity Registration
       ↓
Address, Contact, GST, PAN
       ↓
Basic Company Profile
       ↓
Ready for Financial & Credit Assessment
```

### 2. Document Processing (Module 5-6) → Credit Scoring
```
Document Upload → OCR → Table Extraction → LLM Analysis
         ↓              ↓                    ↓
  Balance Sheet   PnL Statement      Financial Metrics
  Bank Statements Auditor Reports     Extracted Data
  ITRs            Board Minutes         Cash Flows
         ↓                              ↓
         └──────────────┬───────────────┘
                        v
              Financial Ratios &
              Metrics (stored in DB)
                        ↓
              Credit Scoring Input
```

### 3. Financial Metrics Engine (Module 7) → Credit Scoring
```
Extracted Financial Data
         ↓
Ratio Calculations:
- Profitability (Profit Margin, ROA, ROE)
- Liquidity (Current Ratio, Quick Ratio)
- Solvency (Debt-to-Equity, Interest Coverage)
- Efficiency (Asset Turnover, Days Receivable)
         ↓
    Stored in Database
         ↓
Credit Scoring Component 1:
Financial Strength Score (20% weight)
```

### 4. Credit Scoring Orchestration
```
Financial Metrics → Financial Strength Score (20%)
Bank Relations  → Bank Relationship Score (15%)
Industry Data   → Industry Risk Score (15%)
Management Info → Management Quality Score (10%)
Collateral Info → Collateral Strength Score (10%)
Legal Check     → Legal Risk Score (10%)
Fraud Indicators→ Fraud Risk Score (10%)
Credit Bureau   → Credit History Score (10%)
         ↓
    Apply Weights (8 components)
         ↓
    Final Credit Score (0-100)
         ↓
    POD Calculation
         ↓
    Risk Category (AAA-D)
         ↓
    Underwriting Recommendation
```

## Integration Points with Previous Modules

### Financial Metrics Engine (Module 7) Integration

**Data Consumption:**
```python
# From financial_metrics service
metrics = {
    'revenue': 1000000,
    'net_profit': 100000,
    'ebitda': 150000,
    'total_assets': 5000000,
    'total_liabilities': 2000000,
    'profit_margin': 0.10,
    'roa': 0.02,
    'roe': 0.05,
    'debt_to_equity': 0.4,
    'current_ratio': 1.8,
    'quick_ratio': 1.2,
    'interest_coverage': 5.0,
    'working_capital': 500000
}

# Used in CreditScoringEngine
financial_strength_score = scorer.calculate_financial_score(metrics)
```

**Frontend Integration:**
```jsx
import { financialMetricsService } from '@/services/financialMetricsService';
import { creditScoringService } from '@/services/creditScoringService';

// Step 1: Get financial metrics for entity
const metrics = await financialMetricsService.getEntityMetrics(entityId);

// Step 2: Use in credit scoring
const scoringInput = {
  entity_id: entityId,
  financial_metrics: metrics,
  // ... other inputs
};

const creditScore = await creditScoringService.calculateCreditScore(scoringInput);
```

### Document Processing Integration (Module 5-6)

**Data Flow:**
```
Document Upload
    ↓ (OCR + Table Extraction)
Financial Data Extraction
    ↓ (LLM Validation)
Structured Financial Data
    ↓ (Financial Metrics Engine)
Calculated Ratios & Metrics
    ↓ (Credit Scoring Engine)
Credit Score & Recommendation
```

**Frontend Component Integration:**
```jsx
import { DocumentExtractionProcessor } from '@/components/DocumentExtractionProcessor';
import { UnderwritingDashboard } from '@/components/UnderwritingDashboard';

export function CompleteUnderwritingFlow() {
  const [entityId, setEntityId] = useState(null);
  const [documentProcessed, setDocumentProcessed] = useState(false);

  return (
    <div>
      {/* Step 1: Upload and process documents */}
      <DocumentExtractionProcessor
        entityId={entityId}
        onProcessingComplete={() => setDocumentProcessed(true)}
      />

      {/* Step 2: Generate credit score and recommendation */}
      {documentProcessed && (
        <UnderwritingDashboard
          entityId={entityId}
          entityName="Company Name"
        />
      )}
    </div>
  );
}
```

### Entity Onboarding Integration (Module 2)

**Data Available from OnboardingFlow:**
```jsx
// Entity data collected in Module 2
const entityData = {
  company_name: 'ABC Corp',
  registration_number: 'CIN123456',
  gst_number: 'GST123456',
  pan_number: 'PAN123456',
  industry: 'MANUFACTURING',
  annual_revenue: 1000000,
  employees_count: 50,
  incorporation_date: '2015-01-01',
  registered_office: 'Address',
  promoters: [{
    name: 'John Doe',
    years_experience: 15,
    education: 'MBA'
  }]
};

// Used in Credit Scoring
const managementQualityScore = calculateManagementQuality(
  entityData.promoters[0]
);

const industryRiskScore = calculateIndustryRisk(
  entityData.industry,
  entityData.annual_revenue
);
```

## Backend Integration Architecture

### Database Schema Relationships

```
entities (Module 2)
  ├── id (PK)
  ├── company_name
  ├── industry
  └── annual_revenue
         ↓ (FK)
financial_metrics (Module 7)
  ├── id (PK)
  ├── entity_id (FK)
  ├── revenue
  ├── profit_margin
  └── calculated_at
         ↓ (FK)
documents (Module 4-6)
  ├── id (PK)
  ├── entity_id (FK)
  ├── file_path (MinIO)
  └── extracted_data
         ↓ (FK)
credit_scores (Module 8)
  ├── id (PK)
  ├── entity_id (FK)
  ├── document_id (FK)
  ├── credit_score
  ├── component_scores (JSON)
  ├── probability_of_default
  ├── risk_category
  └── calculated_at
         ↓
credit_scoring_history (Module 8)
  ├── id (PK)
  ├── credit_score_id (FK)
  ├── score_change
  └── created_at
         ↓
underwriting_decisions (Module 8)
  ├── id (PK)
  ├── credit_score_id (FK)
  ├── decision
  └── created_at
```

### API Endpoint Integration

**Typical Request Flow:**

```
1. GET /api/entities/{entity_id}
   ↓ Get entity basic info
   
2. GET /api/financial-metrics/entity/{entity_id}/latest
   ↓ Get latest financial metrics (Module 7)
   
3. GET /api/documents/{entity_id}
   ↓ Get supporting documents (Module 5)
   
4. POST /api/credit-scoring/calculate
   ├─ Consume: Entity data + Financial metrics + Document data
   └─ Produce: Credit score + Components + Recommendation
   
5. GET /api/credit-scoring/entity/{entity_id}
   ↓ Get latest credit score for entity
   
6. POST /api/credit-scoring/underwriting-decision
   ├─ Record: Approval decision + Terms + Conditions
   └─ Store: Decision for future reference
```

## Step-by-Step Integration Example

### Complete Underwriting Workflow

```jsx
import React, { useState, useEffect } from 'react';
import { documentProcessor } from '@/services/documentProcessingService';
import { financialMetrics } from '@/services/financialMetricsService';
import { creditScoring } from '@/services/creditScoringService';

export function CompleteUnderwritingWorkflow({ entityId }) {
  const [stage, setStage] = useState('documents'); // documents | metrics | scoring
  const [entity, setEntity] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [creditScore, setCreditScore] = useState(null);
  const [loading, setLoading] = useState(false);

  // Stage 1: Load entity details
  useEffect(() => {
    async function loadEntity() {
      const data = await fetch(`/api/entities/${entityId}`);
      setEntity(await data.json());
    }
    loadEntity();
  }, [entityId]);

  // Stage 2: Process documents and extract financials
  const handleDocumentsProcessed = async () => {
    setLoading(true);
    try {
      // Documents are processed in Module 5-6
      // Financial metrics are automatically calculated in Module 7
      const metricsData = await financialMetrics.getEntityMetrics(entityId);
      setMetrics(metricsData);
      setStage('metrics');
    } finally {
      setLoading(false);
    }
  };

  // Stage 3: Calculate credit score
  const handleCalculateScore = async () => {
    setLoading(true);
    try {
      const scoringResult = await creditScoring.calculateCreditScore({
        entity_id: entityId,
        document_id: latestDocumentId,
        financial_metrics: metrics,
        bank_relationship: {
          years_with_bank: 5,
          facility_types: ['WORKING_CAPITAL'],
          repayment_history: 'EXCELLENT',
          complaint_count: 0
        },
        industry_data: {
          industry: entity.industry,
          sector_growth_rate: 8.5,
          regulatory_environment: 'MEDIUM'
        },
        // ... other components
      });
      setCreditScore(scoringResult);
      setStage('scoring');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {stage === 'documents' && (
        <DocumentProcessingPanel onComplete={handleDocumentsProcessed} />
      )}
      {stage === 'metrics' && (
        <FinancialMetricsReview
          metrics={metrics}
          onContinue={handleCalculateScore}
        />
      )}
      {stage === 'scoring' && (
        <UnderwritingDecisionPanel creditScore={creditScore} />
      )}
    </div>
  );
}
```

## Configuration & Environment

### Frontend Environment Variables
```env
# .env.local or .env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENVIRONMENT=development
REACT_APP_LOG_LEVEL=debug
```

### Backend Configuration
```python
# settings.py
CREDIT_SCORING_CONFIG = {
    'enable_scoring': True,
    'min_data_completeness': 0.70,  # 70% data required
    'confidence_threshold': 0.50,
    'aml_check_enabled': True,
    'fraud_check_enabled': True,
}

FINANCIAL_METRICS_CONFIG = {
    'calculation_method': 'standard',
    'ratio_precision': 2,
    'historical_periods': 3,
}
```

## Dependency Matrix

| Module | Depends On | Provides To |
|--------|-----------|------------|
| Module 2: Onboarding | None | Module 8 (entity data) |
| Module 5-6: Doc Processing | Module 2 | Module 7 (raw financials) |
| Module 7: Financial Metrics | Module 5-6 | Module 8 (calculated metrics) |
| Module 8: Credit Scoring | Module 2, 5-6, 7 | Reports, Dashboards |

## Testing Integration

### Unit Test Example
```python
# test_credit_scoring_integration.py
import pytest
from app.credit_scoring import CreditScoringEngine
from app.services.financial_metrics import FinancialMetricsService

def test_credit_scoring_with_real_metrics():
    """Test credit scoring using real financial metrics"""
    
    # Get financial metrics from Module 7
    metrics_service = FinancialMetricsService()
    metrics = metrics_service.get_metrics(entity_id=123)
    
    # Initialize scoring engine
    engine = CreditScoringEngine()
    
    # Calculate score
    result = engine.calculate_credit_score({
        'financial_metrics': metrics,
        'bank_relationship_data': {...},
        'industry_data': {...}
    })
    
    # Assertions
    assert result['credit_score'] >= 300
    assert result['credit_score'] <= 1000
    assert 'component_scores' in result
    assert result['probability_of_default'] >= 0
    assert result['probability_of_default'] <= 100
```

### Integration Test
```python
def test_end_to_end_underwriting():
    """Test complete workflow from entity to credit decision"""
    
    # 1. Create entity (Module 2)
    entity = create_test_entity()
    
    # 2. Upload document (Module 4)
    doc = upload_test_document(entity.id)
    
    # 3. Process document (Module 5-6)
    extraction = process_document(doc.id)
    assert extraction.status == 'completed'
    
    # 4. Get financial metrics (Module 7)
    metrics = get_financial_metrics(entity.id)
    assert metrics is not None
    
    # 5. Calculate credit score (Module 8)
    score = calculate_credit_score(
        entity_id=entity.id,
        document_id=doc.id,
        financial_metrics=metrics
    )
    assert score.credit_score >= 300
    assert score.decision in ['APPROVED', 'CONDITIONAL', 'DECLINE']
```

## Performance Considerations

### Caching Strategy
```python
# Cache financial metrics for 24 hours
@cache.cached(timeout=86400, key_prefix='financial_metrics_')
def get_entity_metrics(entity_id):
    return FinancialMetricsService().get_metrics(entity_id)

# Cache credit scores for 1 hour (for scoring frequency control)
@cache.cached(timeout=3600, key_prefix='credit_score_')
def get_latest_credit_score(entity_id):
    return CreditScore.query.filter_by(entity_id=entity_id).first()
```

### Database Indexes
```sql
-- Improve query performance
CREATE INDEX idx_credit_score_entity ON credit_scores(entity_id);
CREATE INDEX idx_credit_score_calculated ON credit_scores(calculated_at);
CREATE INDEX idx_financial_metrics_entity ON financial_metrics(entity_id);
CREATE INDEX idx_document_entity ON documents(entity_id);
```

## Migration Path from Previous Versions

If upgrading from a system without Module 8:

1. Install credit scoring package
2. Run database migrations to create credit_scores and credit_scoring_history tables
3. Deploy backend API endpoints
4. Deploy frontend components
5. Import historical financial data for backtesting (optional)
6. Enable credit scoring feature flag

```python
# Feature flag in admin panel
FEATURE_FLAGS = {
    'credit_scoring_enabled': True,
    'auto_calculate_on_metrics_update': False,
    'require_analyst_review': True,
}
```

## Support & Troubleshooting

### Common Integration Issues

**Q: Financial metrics not available when calculating score**
A: Ensure Module 7 has completed metric calculations. Check `financial_metrics` table for entity's most recent entry.

**Q: Score fluctuates significantly between updates**
A: This is normal due to data precision. Set minimum score change threshold (5 points) before recalculation.

**Q: Credit scoring takes too long**
A: Implement caching and consider using quick-score endpoint with financial metrics only.

---

**Integration Guide Version:** 1.0
**Last Updated:** January 2024
