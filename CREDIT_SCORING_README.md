# Credit Scoring & Underwriting Module

## Overview

The Credit Scoring & Underwriting Module is a production-grade system for assessing credit risk using an 8-component weighted scoring model. It combines financial analysis, bank relationships, industry assessment, management quality, collateral evaluation, legal compliance, fraud detection, and credit bureau data to produce a comprehensive credit risk score.

## Architecture

### 8-Component Scoring System

| Component | Weight | Description |
|-----------|--------|-------------|
| Financial Strength | 20% | Profitability, liquidity, solvency ratios |
| Bank Relationship | 15% | Years with bank, facilities, repayment history |
| Industry Risk | 15% | Sector growth, regulatory environment |
| Management Quality | 10% | Experience, education, track record |
| Collateral Strength | 10% | Collateral type, value, LTV ratio |
| Legal Risk | 10% | Litigation, violations, compliance |
| Fraud Risk | 10% | Fraud history, AML compliance |
| Credit Bureau | 10% | CIBIL score, enquiries, defaults |

**Total: 100%**

### Scoring Formula

```
Final Score = (20% × FS) + (15% × BR) + (15% × IR) + (10% × MQ) + 
              (10% × CS) + (10% × LR) + (10% × FR) + (10% × CB)

where: FS=Financial Strength, BR=Bank Relationship, IR=Industry Risk, etc.
```

### Probability of Default (POD)

```
POD % = 100 / (1 + e^(score/25))
```

This logistic function produces:
- Score 100 → ~1% default probability
- Score 50 → ~50% default probability  
- Score 0 → ~99% default probability

### Risk Categories

| Grade | Score Range | Risk Level | PD Range |
|-------|------------|-----------|----------|
| AAA | 850-1000 | Minimal | 0-1% |
| AA | 750-849 | Very Low | 1-2% |
| A | 650-749 | Low | 2-5% |
| BBB | 550-649 | Moderate | 5-10% |
| BB | 450-549 | High | 10-20% |
| B | 350-449 | Very High | 20-40% |
| CCC | 250-349 | Severe | 40-75% |
| D | 0-249 | Default | 75-100% |

## Frontend Components

### UnderwritingDashboard

Main dashboard component combining all credit scoring features.

```jsx
import { UnderwritingDashboard } from './components/UnderwritingDashboard';

<UnderwritingDashboard 
  entityId={123}
  entityName="Company Name"
  onNavigate={(view) => console.log(view)}
/>
```

**Features:**
- Credit score display with risk category
- Score history with trend visualization
- Scoring methodology documentation
- Personalized lending recommendations
- Underwriting decision recording

**Views:**
1. **Scoring** - Latest credit score and component breakdown
2. **History** - Score evolution with trend analysis
3. **Methodology** - Detailed component descriptions and rating scale
4. **Recommendations** - Lending decision guidance and terms

### CreditScoringDisplay

Detailed score card and component analysis component.

```jsx
import { CreditScoringDisplay } from './components/CreditScoringDisplay';

<CreditScoringDisplay
  entityId={123}
  entityName="Company Name"
  onScoringComplete={() => handleRefresh()}
/>
```

**Sections:**
- Main score card (score, grade, POD)
- Component scores grid (8 components)
- Tabbed analysis (overview, risk drivers, strengths, improvements)
- Decision recording modal

## Backend API Endpoints

### Calculate Credit Score
```
POST /api/credit-scoring/calculate
```

**Request:**
```json
{
  "entity_id": 123,
  "document_id": 456,
  "financial_metrics": {
    "revenue": 1000000,
    "net_profit": 100000,
    "total_assets": 5000000,
    ...
  },
  "bank_relationship": {
    "years_with_bank": 5,
    "facility_types": ["WORKING_CAPITAL", "TERM"],
    "repayment_history": "EXCELLENT",
    "complaint_count": 0
  },
  "industry_data": {
    "industry": "MANUFACTURING",
    "subsector": "TEXTILES",
    "sector_growth_rate": 8.5,
    "regulatory_environment": "MEDIUM"
  },
  "management_quality": {
    "management_experience": 15,
    "education_level": "MBA",
    "track_record_score": 85
  },
  "collateral_data": {
    "collateral_type": "REAL_ESTATE",
    "collateral_value": 2000000,
    "ltv_ratio": 0.5,
    "lien_status": "CLEAR"
  },
  "legal_compliance": {
    "litigation_count": 0,
    "regulatory_violations": 0,
    "pending_cases": 0
  },
  "fraud_indicators": {
    "fraud_flag": "NO",
    "chargeback_history": 0,
    "aml_risk_level": "LOW"
  },
  "credit_bureau": {
    "cibil_score": 750,
    "bureau_enquiry_count": 2,
    "default_history": "NO"
  }
}
```

**Response:**
```json
{
  "entity_id": 123,
  "credit_score": 720,
  "probability_of_default": 2.5,
  "risk_category": "AA",
  "component_scores": {
    "financial_strength": 80,
    "bank_relationship": 75,
    "industry_risk": 70,
    "management_quality": 85,
    "collateral_strength": 90,
    "legal_risk": 95,
    "fraud_risk": 100,
    "credit_bureau_score": 85
  },
  "decision": "APPROVED",
  "decision_rationale": "Good credit profile...",
  "recommended_conditions": [],
  "calculated_at": "2024-01-15T10:30:00Z"
}
```

### Get Entity Credit Score
```
GET /api/credit-scoring/entity/{entity_id}
```

Returns latest credit score for an entity.

### Get Score History
```
GET /api/credit-scoring/history/{entity_id}?limit=12
```

Returns historical scores with trend analysis.

### Get Recommendations
```
GET /api/credit-scoring/recommendations/{entity_id}
```

Returns personalized lending recommendations based on credit score.

**Response:**
```json
{
  "action": "APPROVE",
  "rationale": "Good credit profile with moderate risk",
  "conditions": [
    "Financial covenants on debt-to-equity ratio",
    "Annual financial audits"
  ],
  "risk_factors": [],
  "risk_mitigants": ["Good liquidity position"],
  "monitoring_parameters": ["Quarterly financial reviews"],
  "recommended_terms": [
    {
      "parameter": "Interest Rate Adjustment",
      "value": "+100 basis points"
    }
  ]
}
```

### Record Underwriting Decision
```
POST /api/credit-scoring/underwriting-decision
```

**Request:**
```json
{
  "credit_score_id": 789,
  "decision": "APPROVED",
  "decision_reason": "Strong financial position with solid collateral",
  "proposed_interest_rate": 11.5,
  "proposed_loan_amount": 500000,
  "approval_conditions": ["Quarterly financial reporting"]
}
```

### Get Scoring Methodology
```
GET /api/credit-scoring/scoring-methodology
```

Returns detailed documentation of scoring components and methodology.

## Service Layer Usage

### JavaScript Service Methods

```javascript
import { creditScoringService } from '@/services/creditScoringService';

// Calculate score
const result = await creditScoringService.calculateCreditScore({
  entity_id: 123,
  financial_metrics: {...},
  bank_relationship: {...},
  // ... other inputs
});

// Get latest score
const score = await creditScoringService.getEntityCreditScore(123);

// Get score history
const history = await creditScoringService.getCreditScoreHistory(123, 12);

// Get recommendations
const recommendations = await creditScoringService.getRecommendations(123);

// Get methodology
const methodology = await creditScoringService.getScoringMethodology();

// Create decision
const decision = await creditScoringService.createUnderwritingDecision({
  credit_score_id: 789,
  decision: 'APPROVED',
  decision_reason: 'Strong financials',
  proposed_interest_rate: 11.5
});

// Helper methods
creditScoringService.getRiskCategoryColor(category); // Tailwind color class
creditScoringService.getRiskCategoryBadge(category); // Tailwind badge class
creditScoringService.getDecisionDisplay(decision);    // Formatted decision text
creditScoringService.formatPD(pd);                    // Formatted PD%
creditScoringService.assessmentFromScores(scores);    // Component assessments
```

## Decision Rules

| Score Range | Risk Level | Recommendation |
|------------|-----------|----------------|
| 850+ | Minimal | **APPROVED** - Standard terms, quick processing |
| 750-849 | Very Low | **APPROVED** - Standard terms with minor conditions |
| 650-749 | Low | **APPROVED** - Standard conditions, quarterly reporting |
| 550-649 | Moderate | **CONDITIONAL** - Enhanced conditions, higher rate |
| 450-549 | High | **CONDITIONAL** - Strong conditions, reduced amount |
| 350-449 | Very High | **LIKELY DECLINE** - Unless backed by strong mitigants |
| <350 | Severe | **DECLINE** - Unacceptable risk |

## Data Requirements

### Always Required
- Entity financial metrics (revenue, profit, assets)
- CIBIL / Credit bureau score
- Years with bank

### Important
- Collateral information
- Management details
- Industry classification

### Optional (affects confidence score)
- Detailed litigation history
- Fraud investigation records
- Detailed facility utilization data

## Integration Example

```jsx
import React from 'react';
import { UnderwritingDashboard } from '@/components/UnderwritingDashboard';
import { EntityDetailContext } from '@/context/EntityContext';

export function CreditAssessmentPage() {
  const { entity } = React.useContext(EntityDetailContext);
  
  return (
    <div className="min-h-screen bg-gray-100">
      <UnderwritingDashboard
        entityId={entity.id}
        entityName={entity.company_name}
        onNavigate={(view) => {
          console.log(`Navigated to ${view}`);
        }}
      />
    </div>
  );
}
```

## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|-----------|
| Entity not found | Invalid entity_id | Verify entity exists |
| No credit score found | Scoring not performed | Calculate score first |
| Missing required fields | Incomplete input data | Provide all required data |
| Unauthorized | User lacks credit analyst role | Request elevated permissions |
| Calculation failed | Invalid data values | Validate input ranges |

### Example Error Response

```json
{
  "detail": "Entity not found",
  "status_code": 404,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Best Practices

1. **Data Validation**: Ensure all input data is within valid ranges before scoring
2. **Documentation**: Always document the reason for underwriting decisions
3. **Monitoring**: Set up quarterly review for all approved facilities
4. **Trend Analysis**: Monitor score changes over time for early warning signals
5. **Collateral Verification**: Independently verify collateral valuations
6. **Legal Review**: Have legal team review high-risk or large deals

## Limitations

- Scoring based on current snapshot; requires regular updates
- Does not account for macroeconomic shocks
- Collateral risk depends on market conditions
- Management quality assessments are subjective

## Future Enhancements

- [ ] Stress testing module for scenario analysis
- [ ] SHAP-based explainability dashboard
- [ ] Portfolio-level risk concentration analysis
- [ ] Automated covenant monitoring system
- [ ] Machine learning-based rate optimization
- [ ] Real-time risk alerts and early warning system

## Support & Maintenance

For issues or enhancements, contact the Credit Risk Analytics team.

**Last Updated:** January 2024
**Version:** 1.0
