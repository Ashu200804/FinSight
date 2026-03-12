# Explainability Module - SHAP-Based Credit Decision Explanations

## Overview

The Explainability Module provides comprehensive, human-readable explanations for AI-driven credit underwriting decisions using **SHAP (SHapley Additive exPlanations)** values. This module enables credit committees and regulators to understand exactly how the credit scoring model arrived at each decision.

**Status:** ✅ PRODUCTION READY

## Key Features

### 1. Feature Importance Analysis
- **SHAP Values**: Calculates exact contribution of each feature to the prediction
- **Impact Levels**: CRITICAL, HIGH, MEDIUM, LOW rankings
- **Directional Analysis**: Shows whether each feature increases or decreases creditworthiness
- **Normalized Scoring**: 0-100 importance scale for easy comparison

### 2. Human-Readable Explanations
- **Executive Summary**: Plain-English explanation of the decision
- **Key Findings**: Top 3-5 factors driving the decision
- **Strengths & Concerns**: Organized list of positive/negative factors
- **Recommendations**: Specific actions for credit committee

### 3. Risk Factor Identification
- **Automatic Detection**: Identifies financial, legal, and operational risks
- **Severity Grading**: CRITICAL, HIGH, MEDIUM, LOW classification
- **Root Cause Analysis**: Links risks to underlying metrics
- **Mitigation Guidance**: Specific recommendations per risk

### 4. Sensitivity Analysis
- **What-If Analysis**: Shows how score changes with metric variations
- **Elasticity Measurement**: Quantifies impact magnitude
- **Range Analysis**: -30% to +30% variations on key metrics
- **Decision Impact**: Identifies metrics that could change the decision

### 5. LLM SWOT Analysis
- **Input Fusion**: Uses financial metrics, market sentiment, and industry data
- **LLM Generation**: Produces contextual SWOT with concise decision-ready bullets
- **Deterministic Fallback**: If LLM is unavailable, rule-based SWOT still returns results
- **Committee-Friendly Output**: Strengths, Weaknesses, Opportunities, Threats

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Explainability Module                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Request Handler (API Routes)                │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                   │
│  ┌──────────────┴───────────────────────────────┐  │
│  │  Credit Decision Explainer                   │  │
│  │  - Explanation generation                    │  │
│  │  - Risk factor identification                │  │
│  │  - Recommendation engine                     │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                   │
│  ┌──────────────┴───────────────────────────────┐  │
│  │  SHAP Explainer (Feature Importance)         │  │
│  │  - TreeExplainer (XGBoost, LightGBM)         │  │
│  │  - KernelExplainer (Any Model)               │  │
│  │  - SHAP value calculation                    │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                   │
│  ┌──────────────┴───────────────────────────────┐  │
│  │  Credit Scoring Model                        │  │
│  │  (from Module 8)                             │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Database Storage (Audit Trail)              │  │
│  │  - ExplanationModel                          │  │
│  │  - FeatureImportanceModel                    │  │
│  │  - RiskFactorModel                           │  │
│  │  - ExplanationAuditLog                       │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. SHAPExplainer
```python
explainer = SHAPExplainer(
    model=credit_model,
    feature_names=['debt_to_equity', 'current_ratio', ...],
    background_data=sample_data
)

# Get SHAP values
shap_values = explainer.explain_prediction(X)

# Get feature importance
importances = explainer.get_feature_importance(X, prediction_score)
```

**Supports:**
- Tree-based models (XGBoost, LightGBM, Random Forest)
- Neural networks (with KernelExplainer fallback)
- Custom models with predict() method

### 2. CreditDecisionExplainer
```python
explainer = CreditDecisionExplainer(shap_explainer)

explanation = explainer.explain_credit_decision(
    decision_id='DEC-2024-001',
    applicant_name='ABC Corp',
    X=features_df,
    credit_score=750,
    credit_rating='A',
    decision='APPROVE',
    metrics={...},
    research_findings={...}
)
```

**Returns:**
- Feature importance rankings
- Top contributing factors
- Risk factors with mitigation strategies
- Human-readable executive summary
- Sensitivity analysis results

### 3. Database Models

#### ExplanationModel
Stores the complete explanation for audit trail:
- Executive summary
- Feature importance data
- Risk factor assessments
- Recommendations
- Sensitivity analysis

#### FeatureImportanceModel
Individual feature detail:
- Feature name and value
- SHAP value (contribution)
- Importance score (0-100)
- Direction (POSITIVE/NEGATIVE)
- Impact level (CRITICAL-LOW)

#### RiskFactorModel
Identified risks:
- Risk name and category
- Severity level
- Description
- Recommendations
- Supporting metrics

## API Endpoints

### 1. Generate Explanation
```
POST /api/explainability/explain-decision
Content-Type: application/json

{
  "entity_id": 123,
  "credit_score": 750,
  "credit_rating": "A",
  "decision": "APPROVE",
  "features": {
    "debt_to_equity": 1.2,
    "current_ratio": 1.8,
    ...
  },
  "feature_names": [
    "debt_to_equity",
    "current_ratio",
    ...
  ],
  "metrics": {
    "debt_to_equity": 1.2,
    "current_ratio": 1.8,
    ...
  }
}
```

**Response:**
```json
{
  "decision_id": "EXP-2024-001",
  "final_score": 750,
  "final_rating": "A",
  "decision": "APPROVE",
  "feature_importance": [
    {
      "feature_name": "debt_to_equity",
      "importance_score": 95.5,
      "contribution": 0.245,
      "direction": "NEGATIVE",
      "impact_level": "CRITICAL"
    },
    ...
  ],
  "top_risk_factors": [
    {
      "factor_name": "High Financial Leverage",
      "severity": "MEDIUM",
      "description": "...",
      "recommendation": "..."
    }
  ],
  "executive_summary": "...",
  "key_findings": [...],
  "strengths": [...],
  "concerns": [...],
  "recommendations": [...],
  "sensitivity_analysis": {...},
  "explanation_confidence": 0.92
}
```

### 2. Get Stored Explanation
```
GET /api/explainability/explanation/{id}
```

### 3. Get Latest Explanation
```
GET /api/explainability/entity/{entity_id}/latest-explanation
```

### 4. Sensitivity Analysis
```
POST /api/explainability/sensitivity-analysis

{
  "decision_id": "EXP-2024-001",
  "metric_name": "debt_to_equity",
  "variation_percentages": [-30, -20, -10, 10, 20, 30]
}
```

### 5. Risk Factor Analysis
```
POST /api/explainability/risk-factor-analysis

{
  "entity_id": 123,
  "include_mitigants": true
}
```

### 6. Feature Importance
```
GET /api/explainability/feature-importance/{entity_id}?limit=10
```

### 7. Batch Explanations
```
POST /api/explainability/batch-explanations

{
  "entity_ids": [123, 124, 125],
  "include_sensitivity": true
}
```

### 8. Generate SWOT Analysis (LLM)
```
POST /api/explainability/swot-analysis

{
  "entity_id": 123,
  "company_name": "Acme Manufacturing Pvt Ltd",
  "financial_metrics": {
    "debt_to_equity": 1.2,
    "current_ratio": 1.8,
    "debt_service_coverage_ratio": 1.9,
    "net_profit_margin": 0.11
  },
  "market_sentiment": {
    "composite_sentiment_score": 0.42,
    "market_tone": "POSITIVE",
    "analyst_rating": "BUY"
  },
  "industry_data": {
    "industry": "Manufacturing",
    "growth_rate_cagr": 9.5,
    "market_attractiveness": "ATTRACTIVE",
    "regulatory_environment": "NEUTRAL"
  },
  "model": "gpt-4o-mini"
}
```

**Response:**
```json
{
  "company_name": "Acme Manufacturing Pvt Ltd",
  "strengths": [
    "Healthy liquidity profile supports short-term obligations",
    "Moderate leverage supports balance-sheet resilience"
  ],
  "weaknesses": [
    "Debt service headroom can tighten under downside scenarios"
  ],
  "opportunities": [
    "Industry growth trajectory supports selective expansion"
  ],
  "threats": [
    "Input-cost and macro volatility can pressure margins"
  ],
  "generated_at": "2026-03-11T10:30:00",
  "model_used": "gpt-4o-mini"
}
```

## Configuration

Set `OPENAI_API_KEY` in backend environment variables to enable LLM SWOT generation.
If not set, the API automatically returns a rule-based SWOT response.

## Frontend Components

### ExplainabilityDashboard
Main component displaying SHAP analysis with 4 tabs:

1. **Overview Tab**
   - Executive summary
   - Key findings
   - Strengths, concerns, recommendations
   - Top contributing factors

2. **Feature Importance Tab**
   - Ranked importance chart
   - SHAP contribution values
   - Impact levels
   - Visual importance bars

3. **Risk Analysis Tab**
   - Risk factor cards with severity
   - Mitigating factors
   - Specific recommendations
   - Risk categories

4. **Sensitivity Tab**
   - What-if analysis
   - Impact of metric variations
   - Score sensitivity curves
   - Elasticity metrics

## Usage Examples

### Backend Usage

```python
from app.explainability import CreditDecisionExplainer, SHAPExplainer
import pandas as pd

# Initialize explainers
shap_exp = SHAPExplainer(model, feature_names, background_data)
credit_exp = CreditDecisionExplainer(shap_exp)

# Get explanation
explanation = credit_exp.explain_credit_decision(
    decision_id='DEC-2024-001',
    applicant_name='Company Name',
    X=pd.DataFrame([features]),
    credit_score=750,
    credit_rating='A',
    decision='APPROVE',
    metrics=financial_metrics
)

# Access components
print(explanation.executive_summary)
print(explanation.feature_importance)
print(explanation.top_risk_factors)
```

### Frontend Usage

```jsx
import { ExplainabilityDashboard } from '@/components/ExplainabilityDashboard';

function CreditDecisionPage({ decisionId, entityId, entityName }) {
  return (
    <ExplainabilityDashboard
      entityId={entityId}
      entityName={entityName}
      creditDecisionId={decisionId}
      onClose={() => navigate('/decisions')}
    />
  );
}
```

### API Usage

```bash
# Generate explanation
curl -X POST http://localhost:8000/api/explainability/explain-decision \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": 123,
    "credit_score": 750,
    "credit_rating": "A",
    "decision": "APPROVE",
    "features": {...},
    "metrics": {...}
  }'

# Get feature importance
curl -X GET http://localhost:8000/api/explainability/feature-importance/123 \
  -H "Authorization: Bearer TOKEN"

# Perform sensitivity analysis
curl -X POST http://localhost:8000/api/explainability/sensitivity-analysis \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "EXP-2024-001",
    "metric_name": "debt_to_equity",
    "variation_percentages": [-30, -20, 20, 30]
  }'
```

## Feature Importance Interpretation

### Importance Score (0-100)
- **90-100**: Critical impact on decision
- **70-89**: Major impact
- **50-69**: Significant impact
- **30-49**: Moderate impact
- **0-29**: Minor impact

### SHAP Contribution
- **Positive value**: Increases probability of approval
- **Negative value**: Decreases probability of approval
- **Zero**: No impact on prediction

### Direction
- **POSITIVE**: Feature value is favorable
- **NEGATIVE**: Feature value is unfavorable
- **NEUTRAL**: Mixed impact

## Risk Factor Severity

- **CRITICAL**: Decision must be reconsidered
- **HIGH**: Significant concern requiring mitigation
- **MEDIUM**: Notable issue, monitor closely
- **LOW**: Minor issue, standard monitoring

## Integration with Credit Scoring

The explainability module enhances the credit scoring (Module 8) by:

1. **Transparency**: Shows exactly which metrics matter
2. **Validation**: Confirms financial metrics are being used correctly
3. **Audit Trail**: Maintains record of explanation methodology
4. **Regulatory Compliance**: Provides documentation for credit regulators

## Configuration

### Environment Variables

```env
# Model Configuration
CREDIT_MODEL_PATH=/models/credit_scorer.pkl
CREDIT_MODEL_VERSION=1.0
CREDIT_MODEL_TYPE=xgboost

# SHAP Configuration
SHAP_BACKGROUND_SIZE=100
SHAP_EXPLAINER_TYPE=tree  # tree or kernel

# Caching
ENABLE_EXPLANATION_CACHE=true
EXPLANATION_CACHE_TTL=3600  # seconds

# Logging
EXPLAINABILITY_LOG_LEVEL=INFO
SAVE_EXPLANATIONS_TO_DB=true
```

## Best Practices

### 1. SHAP Calculation
- Use TreeExplainer for tree models (100x faster)
- Use KernelExplainer for other models
- Ensure background data is representative (100-1000 samples)

### 2. Explanation Generation
- Always include financial metrics context
- Link SHAP values to domain interpretations
- Provide specific recommendations per risk factor
- Include confidence scores

### 3. Performance
- Cache explanations for repeated queries
- Use batch operations for multiple decisions
- Implement pagination for large result sets
- Log explanation generation time

### 4. Compliance
- Audit all explanation generations
- Document model versions with explanations
- Retain explanations for regulatory review
- Implement version control for templates

## Dependencies

**Backend:**
```bash
pip install shap pandas numpy scikit-learn
```

**Models:** Requires pre-trained credit scoring model from [Module 8](../credit_scoring/)

## Troubleshooting

### Issue: SHAP values all zeros
- **Cause**: Feature values not in appropriate scale
- **Solution**: Normalize/standardize features before SHAP calculation

### Issue: Explanation generation timeout
- **Cause**: Large background dataset or KernelExplainer
- **Solution**: Reduce background data size or use TreeExplainer

### Issue: Risk factor detection missing some risks
- **Cause**: Default threshold values may not fit your data
- **Solution**: Customize risk detection templates in engine

## Future Enhancements

- [ ] Interactive SHAP force plots visualization
- [ ] Feature interaction analysis (Shapley interactions)
- [ ] Counterfactual explanations (what would change the decision)
- [ ] Partial dependence plots
- [ ] Individual conditional expectation (ICE) curves
- [ ] Model comparison (explaining differences between models)
- [ ] Explanation consistency checks
- [ ] Regulatory report generation

## Files

**Backend (1000+ lines):**
- `explainability_engine.py` - SHAP and explanation logic
- `models.py` - Database models for explanations
- `schemas.py` - Pydantic validation schemas
- `routes.py` - FastAPI endpoints
- `__init__.py` - Module exports

**Frontend (1200+ lines):**
- `ExplainabilityDashboard.jsx` - Main UI component with 4 tabs
- `explainabilityService.js` - API service layer

## Module Status

- ✅ SHAPExplainer for feature importance
- ✅ CreditDecisionExplainer for domain-specific reasoning
- ✅ Risk factor identification engine
- ✅ Sensitivity analysis
- ✅ Database persistence (7 new tables)
- ✅ API endpoints (7+)
- ✅ Frontend dashboard with interactive tabs
- ✅ Batch operations support
- ✅ Audit trail logging

---

**Module 10 (Explainability) - Production Ready**
**Last Updated:** March 2026
**Version:** 1.0
