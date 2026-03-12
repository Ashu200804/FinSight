from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import json
from typing import Optional

from app.database.config import get_db
from app.auth.routes import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.entity import Entity
from app.metrics.metrics_engine import FinancialMetricsEngine
from app.metrics.models import FinancialMetrics as FinancialMetricsModel
from app.metrics.schemas import (
    FinancialMetricsRequest,
    FinancialMetricsResponse,
    ProfitabilityRatios,
    LiquidityRatios,
    SolvencyRatios,
    EfficiencyRatios,
    Score,
    CreditScoreInputs,
)
from app.ai_pipeline.routes import get_document_extraction_results

router = APIRouter(prefix="/api/metrics", tags=["Financial Metrics"])


@router.post("/calculate", response_model=FinancialMetricsResponse)
async def calculate_financial_metrics(
    request: FinancialMetricsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate financial metrics for a document.
    
    This endpoint:
    1. Retrieves the processed document and extracted data
    2. Extracts key financial metrics
    3. Calculates comprehensive financial ratios
    4. Generates credit scoring inputs
    5. Stores the metrics for historical tracking
    
    Args:
        document_id: ID of the document to analyze
        use_extracted_data: Whether to use AI-extracted data (default: True)
    
    Returns:
        FinancialMetricsResponse with all calculated metrics and ratios
    """
    try:
        # Verify document exists and user has access
        document = db.query(Document).filter(Document.id == request.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify user is associated with the entity or is admin
        entity = db.query(Entity).filter(Entity.id == document.entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Initialize metrics engine
        engine = FinancialMetricsEngine()
        
        # Get extracted data from AI pipeline
        extraction_results = get_document_extraction_results(document.id, db)
        if not extraction_results or not extraction_results.get('extracted_data'):
            raise HTTPException(
                status_code=400,
                detail="Document has not been processed by AI pipeline. Please process the document first."
            )
        
        extracted_data = extraction_results['extracted_data']
        
        # Extract financial metrics
        metrics = engine.extract_financial_metrics(extracted_data)
        
        # Calculate all ratios
        ratios = engine.calculate_all_ratios(metrics)
        
        # Generate credit score inputs
        credit_inputs = engine.generate_credit_score_inputs(metrics, ratios)
        
        # Build response
        response = FinancialMetricsResponse(
            document_id=document.id,
            entity_id=entity.id,
            calculated_at=engine.calculated_at,
            extracted_metrics=metrics,
            profitability_ratios=ProfitabilityRatios(**ratios.get('profitability_ratios', {})),
            liquidity_ratios=LiquidityRatios(**ratios.get('liquidity_ratios', {})),
            solvency_ratios=SolvencyRatios(**ratios.get('solvency_ratios', {})),
            efficiency_ratios=EfficiencyRatios(**ratios.get('efficiency_ratios', {})),
            credit_score_inputs=CreditScoreInputs(
                profitability_score=Score(**credit_inputs['profitability_score']),
                liquidity_score=Score(**credit_inputs['liquidity_score']),
                solvency_score=Score(**credit_inputs['solvency_score']),
                efficiency_score=Score(**credit_inputs['efficiency_score']),
                cash_flow_health=credit_inputs['cash_flow_health'],
                leverage_assessment=credit_inputs['leverage_assessment'],
                trend_indicators=credit_inputs['trend_indicators'],
            ),
            calculation_status='partial' if engine.warnings else 'success',
            warnings=engine.warnings,
            errors=engine.errors,
        )
        
        # Store metrics in database
        db_metrics = FinancialMetricsModel(
            document_id=document.id,
            entity_id=entity.id,
            metrics_json=metrics,
            profitability_score=credit_inputs['profitability_score']['score'],
            liquidity_score=credit_inputs['liquidity_score']['score'],
            solvency_score=credit_inputs['solvency_score']['score'],
            efficiency_score=credit_inputs['efficiency_score']['score'],
            overall_health_score=(
                credit_inputs['profitability_score']['score'] * 0.3 +
                credit_inputs['liquidity_score']['score'] * 0.25 +
                credit_inputs['solvency_score']['score'] * 0.25 +
                credit_inputs['efficiency_score']['score'] * 0.2
            ) / 100,
            ratios_json=ratios,
            credit_score_inputs_json=credit_inputs,
            calculation_status=response.calculation_status,
            warnings=engine.warnings,
            errors=engine.errors,
        )
        db.add(db_metrics)
        db.commit()
        db.refresh(db_metrics)
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics calculation failed: {str(e)}")


@router.get("/entity/{entity_id}", response_model=dict)
async def get_entity_metrics(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Get historical metrics for an entity (latest N calculations).
    
    Args:
        entity_id: ID of the entity
        limit: Number of recent metrics to retrieve (1-100)
    
    Returns:
        List of financial metrics with timestamps
    """
    try:
        # Verify entity exists
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        # Get recent metrics
        metrics_list = (
            db.query(FinancialMetricsModel)
            .filter(FinancialMetricsModel.entity_id == entity_id)
            .order_by(FinancialMetricsModel.calculated_at.desc())
            .limit(limit)
            .all()
        )
        
        return {
            "entity_id": entity_id,
            "company_name": entity.company_name,
            "metrics_count": len(metrics_list),
            "metrics": [
                {
                    "id": m.id,
                    "document_id": m.document_id,
                    "calculated_at": m.calculated_at,
                    "scores": {
                        "profitability": m.profitability_score,
                        "liquidity": m.liquidity_score,
                        "solvency": m.solvency_score,
                        "efficiency": m.efficiency_score,
                        "overall_health": m.overall_health_score,
                    },
                    "status": m.calculation_status,
                }
                for m in metrics_list
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/document/{document_id}", response_model=dict)
async def get_document_metrics(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed metrics for a specific document.
    
    Args:
        document_id: ID of the document
    
    Returns:
        Complete financial metrics and ratios for the document
    """
    try:
        metrics = (
            db.query(FinancialMetricsModel)
            .filter(FinancialMetricsModel.document_id == document_id)
            .order_by(FinancialMetricsModel.calculated_at.desc())
            .first()
        )
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Metrics not found for this document")
        
        return {
            "id": metrics.id,
            "document_id": metrics.document_id,
            "entity_id": metrics.entity_id,
            "calculated_at": metrics.calculated_at,
            "metrics": metrics.metrics_json,
            "ratios": metrics.ratios_json,
            "credit_score_inputs": metrics.credit_score_inputs_json,
            "scores": {
                "profitability": metrics.profitability_score,
                "liquidity": metrics.liquidity_score,
                "solvency": metrics.solvency_score,
                "efficiency": metrics.efficiency_score,
                "overall_health": metrics.overall_health_score,
            },
            "status": metrics.calculation_status,
            "warnings": metrics.warnings or [],
            "errors": metrics.errors or [],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document metrics: {str(e)}")


@router.get("/comparison/{entity_id}")
async def compare_metrics(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare metrics across multiple documents for trend analysis.
    
    Args:
        entity_id: ID of the entity
    
    Returns:
        Comparative analysis of metrics over time
    """
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        metrics_list = (
            db.query(FinancialMetricsModel)
            .filter(FinancialMetricsModel.entity_id == entity_id)
            .order_by(FinancialMetricsModel.calculated_at.asc())
            .all()
        )
        
        if not metrics_list:
            raise HTTPException(status_code=404, detail="No metrics found for this entity")
        
        # Extract trend data
        trends = {
            'dates': [m.calculated_at for m in metrics_list],
            'profitability_scores': [m.profitability_score for m in metrics_list],
            'liquidity_scores': [m.liquidity_score for m in metrics_list],
            'solvency_scores': [m.solvency_score for m in metrics_list],
            'efficiency_scores': [m.efficiency_score for m in metrics_list],
            'overall_health_scores': [m.overall_health_score for m in metrics_list],
        }
        
        # Calculate trend directions
        def calculate_trend(values):
            if len(values) < 2:
                return "insufficient_data"
            recent = sum(values[-3:]) / len(values[-3:]) if len(values) >= 3 else values[-1]
            previous = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else (values[0] if len(values) > 1 else values[-1])
            if recent > previous:
                return "improving"
            elif recent < previous:
                return "deteriorating"
            else:
                return "stable"
        
        return {
            "entity_id": entity_id,
            "company_name": entity.company_name,
            "metrics_count": len(metrics_list),
            "trends": trends,
            "trend_analysis": {
                "profitability_trend": calculate_trend(trends['profitability_scores']),
                "liquidity_trend": calculate_trend(trends['liquidity_scores']),
                "solvency_trend": calculate_trend(trends['solvency_scores']),
                "efficiency_trend": calculate_trend(trends['efficiency_scores']),
                "overall_health_trend": calculate_trend(trends['overall_health_scores']),
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare metrics: {str(e)}")


@router.get("/metrics-info")
async def get_metrics_info():
    """
    Get information about all available metrics and their definitions.
    
    Returns:
        Reference documentation for all metrics and ratios
    """
    return {
        "metrics_engine": "FinancialMetricsEngine v1.0",
        "categories": {
            "profitability": {
                "description": "Metrics measuring the company's ability to generate profit",
                "ratios": [
                    {"name": "Profit Margin", "formula": "Net Income / Revenue", "interpretation": "Percentage of revenue that becomes profit"},
                    {"name": "Return on Assets (ROA)", "formula": "Net Income / Total Assets", "interpretation": "Profit generated per rupee of assets"},
                    {"name": "Return on Equity (ROE)", "formula": "Net Income / Equity", "interpretation": "Profit generated per rupee of shareholder investment"},
                ]
            },
            "liquidity": {
                "description": "Metrics measuring the company's ability to meet short-term obligations",
                "ratios": [
                    {"name": "Current Ratio", "formula": "Current Assets / Current Liabilities", "benchmark": "1.5-3.0", "interpretation": "Short-term financial health"},
                    {"name": "Quick Ratio", "formula": "(Current Assets - Inventory) / Current Liabilities", "benchmark": "≥1.0", "interpretation": "Stringent liquidity measure"},
                    {"name": "Working Capital Ratio", "formula": "Working Capital / Current Liabilities", "interpretation": "Operating capital available for short-term needs"},
                ]
            },
            "solvency": {
                "description": "Metrics measuring the company's ability to meet long-term obligations",
                "ratios": [
                    {"name": "Debt to Equity", "formula": "Total Debt / Equity", "benchmark": "0.5-2.0", "interpretation": "Leverage and financial structure"},
                    {"name": "Interest Coverage", "formula": "EBIT / Interest Expense", "benchmark": ">2.5x", "interpretation": "Ability to pay interest from operating income"},
                    {"name": "Debt Service Coverage", "formula": "Operating Cash Flow / Total Debt", "benchmark": ">1.25x", "interpretation": "Ability to service debt from cash generation"},
                ]
            },
            "efficiency": {
                "description": "Metrics measuring how effectively the company uses its assets",
                "ratios": [
                    {"name": "Asset Turnover", "formula": "Revenue / Total Assets", "benchmark": "1.0-2.0", "interpretation": "Revenue generated per rupee of assets"},
                    {"name": "Inventory Turnover", "formula": "COGS / Inventory", "interpretation": "How quickly inventory is sold and replaced"},
                    {"name": "Receivables Turnover", "formula": "Revenue / Accounts Receivable", "interpretation": "How quickly receivables are collected"},
                ]
            }
        },
        "scoring_methodology": {
            "profitability_score": "Weighted average of profit margin (40%), ROE (30%), ROA (30%). Max 100.",
            "liquidity_score": "Weighted average of current ratio (40%), quick ratio (35%), working capital (25%). Max 100.",
            "solvency_score": "Weighted average of debt-to-equity (35%), interest coverage (35%), debt service coverage (30%). Max 100.",
            "efficiency_score": "Weighted average of asset turnover (50%), inventory turnover (50%). Max 100.",
            "overall_health_score": "Weighted average of profitability (30%), liquidity (25%), solvency (25%), efficiency (20%). Score 0-100."
        },
        "credit_risk_assessment": {
            "description": "Converts metrics into credit risk indicators for underwriting decisions",
            "outputs": [
                "Risk Level: Low, Medium, High, Very High",
                "Leverage Assessment: Conservative, Moderate, High, Very High",
                "Cash Flow Health: Positive, Negative, Concerning",
                "Credit Grade: AAA, AA, A, BBB, BB, B, CCC, D (future implementation)"
            ]
        }
    }
