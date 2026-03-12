"""CAM routes for generating, storing, listing, and downloading CAM reports."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.auth.routes import get_current_user
from app.cam.report_generator import CAMReportGenerator
from app.cam.models import CAMReport
from app.cam.schemas import (
    CAMReportHistoryItem,
    CAMReportHistoryResponse,
    CAMPreviewResponse,
    CAMPreviewScorecard,
    CAMPreviewRecommendation,
)
from app.credit_scoring.models import CreditScore, UnderwritingDecision
from app.models.entity import Entity
from app.metrics.models import FinancialMetrics
from app.research_engine.models import ResearchReport, LegalRisk, MarketSentiment, IndustryReport
from app.explainability.models import ExplanationModel, FeatureImportanceModel, RiskFactorModel


router = APIRouter(prefix="/cam", tags=["CAM"])
cam_generator = CAMReportGenerator()
REPORTS_DIR = Path(__file__).resolve().parents[3] / "storage" / "cam_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _compute_approval_probability(credit_score: CreditScore | None) -> float | None:
    if not credit_score or credit_score.probability_of_default is None:
        return None

    pd_value = float(credit_score.probability_of_default)
    if pd_value <= 1:
        approval_prob = 1 - pd_value
    else:
        approval_prob = (100 - pd_value) / 100

    return max(0.0, min(1.0, approval_prob))


@router.get("/preview/{entity_id}", response_model=CAMPreviewResponse, summary="Get CAM preview data")
async def get_cam_preview(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity with id={entity_id} not found")

    financial = (
        db.query(FinancialMetrics)
        .filter(FinancialMetrics.entity_id == entity_id)
        .order_by(FinancialMetrics.calculated_at.desc())
        .first()
    )
    credit_score = db.query(CreditScore).filter(CreditScore.entity_id == entity_id).first()
    underwriting = (
        db.query(UnderwritingDecision)
        .filter(UnderwritingDecision.entity_id == entity_id)
        .order_by(UnderwritingDecision.decision_date.desc())
        .first()
    )
    report = (
        db.query(ResearchReport)
        .filter(ResearchReport.entity_id == entity_id)
        .order_by(ResearchReport.created_at.desc())
        .first()
    )
    sentiment = (
        db.query(MarketSentiment)
        .filter(MarketSentiment.entity_id == entity_id)
        .order_by(MarketSentiment.analysis_date.desc())
        .first()
    )
    industry = (
        db.query(IndustryReport)
        .filter(IndustryReport.entity_id == entity_id)
        .order_by(IndustryReport.created_at.desc())
        .first()
    )
    legal_risks = (
        db.query(LegalRisk)
        .filter(LegalRisk.entity_id == entity_id)
        .order_by(LegalRisk.detection_date.desc())
        .limit(5)
        .all()
    )
    explanation = (
        db.query(ExplanationModel)
        .filter(ExplanationModel.entity_id == entity_id)
        .order_by(ExplanationModel.created_at.desc())
        .first()
    )

    financial_metrics = cam_generator._extract_financial_metrics(financial)
    market_sentiment = cam_generator._extract_market_sentiment(sentiment, report)
    industry_data = cam_generator._extract_industry_data(entity, industry, report)
    swot = cam_generator.swot_generator.generate_swot(
        company_name=entity.company_name,
        financial_metrics=financial_metrics,
        market_sentiment=market_sentiment,
        industry_data=industry_data,
    )

    recommendation_rows = cam_generator._build_loan_recommendation(entity, credit_score, underwriting, legal_risks)
    recommendation_map = {key: value for key, value in recommendation_rows}

    feature_rows = []
    risk_rows = []
    if explanation:
        feature_rows = (
            db.query(FeatureImportanceModel)
            .filter(FeatureImportanceModel.explanation_id == explanation.id)
            .order_by(FeatureImportanceModel.importance_score.desc())
            .limit(5)
            .all()
        )
        risk_rows = (
            db.query(RiskFactorModel)
            .filter(RiskFactorModel.explanation_id == explanation.id)
            .order_by(RiskFactorModel.created_at.desc())
            .limit(5)
            .all()
        )

    financial_analysis = {
        "overall_health_score": float(getattr(financial, "overall_health_score", 0) or 0),
        "profitability_score": float(getattr(financial, "profitability_score", 0) or 0),
        "liquidity_score": float(getattr(financial, "liquidity_score", 0) or 0),
        "solvency_score": float(getattr(financial, "solvency_score", 0) or 0),
        "efficiency_score": float(getattr(financial, "efficiency_score", 0) or 0),
        "debt_to_equity": float(financial_metrics.get("debt_to_equity", 0) or 0),
        "current_ratio": float(financial_metrics.get("current_ratio", 0) or 0),
        "debt_service_coverage_ratio": float(financial_metrics.get("debt_service_coverage_ratio", 0) or 0),
        "net_profit_margin": float(financial_metrics.get("net_profit_margin", 0) or 0),
        "return_on_assets": float(financial_metrics.get("return_on_assets", 0) or 0),
    }

    return CAMPreviewResponse(
        entity_id=entity.id,
        entity_name=entity.company_name,
        generated_at=datetime.utcnow(),
        scorecard=CAMPreviewScorecard(
            credit_score=float(credit_score.credit_score) if credit_score and credit_score.credit_score is not None else None,
            risk_category=credit_score.risk_category if credit_score else None,
            probability_of_default=float(credit_score.probability_of_default) if credit_score and credit_score.probability_of_default is not None else None,
            financial_grade=credit_score.financial_grade if credit_score else None,
            decision=credit_score.decision if credit_score else None,
        ),
        financial_analysis=financial_analysis,
        market_snapshot={
            "tone": str(market_sentiment.get("overall_tone", "NEUTRAL")),
            "sentiment_score": float(market_sentiment.get("composite_sentiment_score", 0) or 0),
            "industry": str(industry_data.get("industry", entity.sector or "General")),
            "industry_cagr": float(industry_data.get("growth_rate_cagr", 0) or 0),
            "market_attractiveness": str(industry_data.get("market_attractiveness", "MODERATE")),
        },
        top_feature_importance=[
            f"{row.feature_name}: {float(row.importance_score or 0):.2f} ({row.direction or 'N/A'})"
            for row in feature_rows
        ],
        top_risk_factors=[
            f"[{row.severity or 'N/A'}] {row.factor_name}: {row.description or 'No details'}"
            for row in risk_rows
        ],
        swot={
            "strengths": [str(item) for item in swot.get("strengths", [])][:5],
            "weaknesses": [str(item) for item in swot.get("weaknesses", [])][:5],
            "opportunities": [str(item) for item in swot.get("opportunities", [])][:5],
            "threats": [str(item) for item in swot.get("threats", [])][:5],
        },
        recommendation=CAMPreviewRecommendation(
            decision=str(recommendation_map.get("Recommended Decision", "REVIEW_REQUIRED")),
            requested_amount=str(recommendation_map.get("Requested Amount", "N/A")),
            suggested_rate_guidance=str(recommendation_map.get("Suggested Rate Guidance", "N/A")),
            key_conditions=str(recommendation_map.get("Key Conditions", "N/A")),
            rationale=str(recommendation_map.get("Rationale", "N/A")),
        ),
    )


@router.get("/generate/{entity_id}", summary="Generate CAM report PDF")
async def generate_cam_report(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate professional CAM PDF and return as downloadable file.

    Endpoint:
    GET /cam/generate/{entity_id}
    """
    try:
        pdf_bytes = cam_generator.generate_cam_pdf(db=db, entity_id=entity_id)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"CAM_Report_Entity_{entity_id}_{timestamp}.pdf"

        report_path = REPORTS_DIR / filename
        report_path.write_bytes(pdf_bytes)

        credit_score = db.query(CreditScore).filter(CreditScore.entity_id == entity_id).first()
        approval_probability = _compute_approval_probability(credit_score)

        cam_report = CAMReport(
            entity_id=entity_id,
            credit_score=float(credit_score.credit_score) if credit_score and credit_score.credit_score is not None else None,
            risk_category=credit_score.risk_category if credit_score else None,
            approval_probability=approval_probability,
            report_path=str(report_path),
        )
        db.add(cam_report)
        db.commit()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CAM report: {str(e)}")


@router.get("/history/{entity_id}", response_model=CAMReportHistoryResponse, summary="Get CAM history for entity")
async def get_cam_history(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reports = (
        db.query(CAMReport)
        .filter(CAMReport.entity_id == entity_id)
        .order_by(CAMReport.created_at.desc())
        .all()
    )

    items = [
        CAMReportHistoryItem(
            id=report.id,
            entity_id=report.entity_id,
            credit_score=report.credit_score,
            risk_category=report.risk_category,
            approval_probability=report.approval_probability,
            created_at=report.created_at,
            download_url=f"/cam/download/{report.id}",
        )
        for report in reports
    ]

    return CAMReportHistoryResponse(
        entity_id=entity_id,
        total_reports=len(items),
        reports=items,
    )


@router.get("/download/{report_id}", summary="Download stored CAM report")
async def download_cam_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    report = db.query(CAMReport).filter(CAMReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="CAM report not found")

    path = Path(report.report_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Report file not found on server")

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=path.name,
    )
