"""
CAM (Credit Appraisal Memorandum) report generator.

Builds a professional PDF report with sections:
- Entity Overview
- Financial Analysis
- Borrowing Profile
- Shareholding Structure
- Secondary Research Insights
- Credit Score
- Explainable AI reasoning
- SWOT analysis
- Loan Recommendation
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from app.models.entity import Entity
from app.metrics.models import FinancialMetrics
from app.credit_scoring.models import CreditScore, UnderwritingDecision
from app.research_engine.models import (
    ResearchReport,
    CompanyNews,
    LegalRisk,
    MarketSentiment,
    IndustryReport,
)
from app.explainability.models import ExplanationModel, FeatureImportanceModel, RiskFactorModel
from app.explainability.explainability_engine import SWOTLLMGenerator


class CAMReportGenerator:
    def __init__(self):
        self.swot_generator = SWOTLLMGenerator()

    def generate_cam_pdf(self, db: Session, entity_id: int) -> bytes:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            raise ValueError(f"Entity with id={entity_id} not found")

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
        research_report = (
            db.query(ResearchReport)
            .filter(ResearchReport.entity_id == entity_id)
            .order_by(ResearchReport.created_at.desc())
            .first()
        )
        explanation = (
            db.query(ExplanationModel)
            .filter(ExplanationModel.entity_id == entity_id)
            .order_by(ExplanationModel.created_at.desc())
            .first()
        )

        recent_news = (
            db.query(CompanyNews)
            .filter(CompanyNews.entity_id == entity_id)
            .order_by(CompanyNews.published_at.desc())
            .limit(5)
            .all()
        )
        legal_risks = (
            db.query(LegalRisk)
            .filter(LegalRisk.entity_id == entity_id)
            .order_by(LegalRisk.detection_date.desc())
            .limit(5)
            .all()
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

        financial_metrics = self._extract_financial_metrics(financial)
        market_sentiment = self._extract_market_sentiment(sentiment, research_report)
        industry_data = self._extract_industry_data(entity, industry, research_report)

        swot = self.swot_generator.generate_swot(
            company_name=entity.company_name,
            financial_metrics=financial_metrics,
            market_sentiment=market_sentiment,
            industry_data=industry_data,
        )

        loan_recommendation = self._build_loan_recommendation(entity, credit_score, underwriting, legal_risks)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title=f"CAM - {entity.company_name}",
            author="Credit Underwriting System",
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], spaceAfter=8))
        styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], leading=14, spaceAfter=4))
        styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=9, textColor=colors.grey))

        story: List[Any] = []

        story.append(Paragraph("Credit Appraisal Memorandum (CAM)", styles["Title"]))
        story.append(Paragraph(f"Entity: {entity.company_name}", styles["Heading3"]))
        story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%d-%b-%Y %H:%M UTC')}", styles["Small"]))
        story.append(Spacer(1, 8))

        self._add_key_value_section(story, styles, "1. Entity Overview", [
            ("Company Name", entity.company_name),
            ("CIN", entity.cin or "N/A"),
            ("PAN", entity.pan or "N/A"),
            ("Sector", entity.sector or "N/A"),
            ("Subsector", entity.subsector or "N/A"),
            ("Turnover", self._fmt_num(entity.turnover)),
            ("Address", entity.address or "N/A"),
        ])

        self._add_key_value_section(story, styles, "2. Financial Analysis", [
            ("Overall Health Score", self._fmt_num(getattr(financial, "overall_health_score", None))),
            ("Profitability Score", self._fmt_num(getattr(financial, "profitability_score", None))),
            ("Liquidity Score", self._fmt_num(getattr(financial, "liquidity_score", None))),
            ("Solvency Score", self._fmt_num(getattr(financial, "solvency_score", None))),
            ("Efficiency Score", self._fmt_num(getattr(financial, "efficiency_score", None))),
            ("Debt to Equity", self._fmt_num(financial_metrics.get("debt_to_equity"))),
            ("Current Ratio", self._fmt_num(financial_metrics.get("current_ratio"))),
            ("DSCR", self._fmt_num(financial_metrics.get("debt_service_coverage_ratio"))),
            ("Net Profit Margin", self._fmt_pct(financial_metrics.get("net_profit_margin"))),
            ("Return on Assets", self._fmt_pct(financial_metrics.get("return_on_assets"))),
        ])

        self._add_key_value_section(story, styles, "3. Borrowing Profile", [
            ("Loan Type", str(entity.loan_type.value) if entity.loan_type else "N/A"),
            ("Requested Loan Amount", self._fmt_inr(entity.loan_amount)),
            ("Tenure (months)", str(entity.tenure) if entity.tenure else "N/A"),
            ("Proposed Interest Rate", self._fmt_pct(entity.interest_rate / 100 if entity.interest_rate else None)),
            ("Purpose of Loan", entity.purpose_of_loan or "N/A"),
            ("Latest Underwriting Decision", underwriting.decision if underwriting else "N/A"),
            ("Proposed Loan Amount", self._fmt_inr(underwriting.proposed_loan_amount if underwriting else None)),
            ("Proposed Tenure", str(underwriting.proposed_tenure) if underwriting and underwriting.proposed_tenure else "N/A"),
        ])

        shareholding = self._extract_shareholding_data(financial, research_report)
        self._add_key_value_section(story, styles, "4. Shareholding Structure", shareholding)

        story.append(Paragraph("5. Secondary Research Insights", styles["SectionTitle"]))
        self._add_bullet_list(story, styles, "Research Highlights", (research_report.key_findings if research_report and research_report.key_findings else []))
        self._add_bullet_list(
            story,
            styles,
            "Recent News",
            [f"{n.published_at.strftime('%d-%b-%Y') if n.published_at else 'N/A'}: {n.title}" for n in recent_news],
        )
        self._add_bullet_list(
            story,
            styles,
            "Legal Risks",
            [f"[{r.severity}] {r.risk_type}: {r.description or 'No details'}" for r in legal_risks],
        )
        story.append(Paragraph(
            f"Market Sentiment: {market_sentiment.get('overall_tone', 'N/A')} (score: {self._fmt_num(market_sentiment.get('composite_sentiment_score'))})",
            styles["Body"],
        ))
        story.append(Paragraph(
            f"Industry Outlook: {industry_data.get('market_attractiveness', 'N/A')} | CAGR: {self._fmt_num(industry_data.get('growth_rate_cagr'))}%",
            styles["Body"],
        ))
        story.append(Spacer(1, 6))

        self._add_key_value_section(story, styles, "6. Credit Score", [
            ("Credit Score", str(getattr(credit_score, "credit_score", "N/A"))),
            ("Risk Category", getattr(credit_score, "risk_category", "N/A")),
            ("Probability of Default", self._fmt_pct((credit_score.probability_of_default / 100) if credit_score and credit_score.probability_of_default is not None else None)),
            ("Financial Grade", getattr(credit_score, "financial_grade", "N/A")),
            ("Decision", getattr(credit_score, "decision", "N/A")),
        ])

        story.append(Paragraph("7. Explainable AI Reasoning", styles["SectionTitle"]))
        if explanation:
            story.append(Paragraph(explanation.executive_summary or "No executive summary available.", styles["Body"]))
            top_features = (
                db.query(FeatureImportanceModel)
                .filter(FeatureImportanceModel.explanation_id == explanation.id)
                .order_by(FeatureImportanceModel.importance_score.desc())
                .limit(5)
                .all()
            )
            self._add_bullet_list(
                story,
                styles,
                "Top Feature Importance",
                [
                    f"{fi.feature_name}: {self._fmt_num(fi.importance_score)} ({fi.direction}, {fi.impact_level})"
                    for fi in top_features
                ],
            )
            top_risks = (
                db.query(RiskFactorModel)
                .filter(RiskFactorModel.explanation_id == explanation.id)
                .order_by(RiskFactorModel.created_at.desc())
                .limit(5)
                .all()
            )
            self._add_bullet_list(
                story,
                styles,
                "Top Contributing Risk Factors",
                [f"[{r.severity}] {r.factor_name}: {r.description}" for r in top_risks],
            )
            self._add_bullet_list(story, styles, "Human-Readable Reasoning", explanation.key_findings or [])
        else:
            story.append(Paragraph("Explainability data is not available for this entity.", styles["Body"]))

        story.append(Paragraph("8. SWOT Analysis", styles["SectionTitle"]))
        self._add_bullet_list(story, styles, "Strengths", swot.get("strengths", []))
        self._add_bullet_list(story, styles, "Weaknesses", swot.get("weaknesses", []))
        self._add_bullet_list(story, styles, "Opportunities", swot.get("opportunities", []))
        self._add_bullet_list(story, styles, "Threats", swot.get("threats", []))

        story.append(Paragraph("9. Loan Recommendation", styles["SectionTitle"]))
        for k, v in loan_recommendation:
            story.append(Paragraph(f"<b>{k}:</b> {v}", styles["Body"]))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _add_key_value_section(self, story: List[Any], styles, title: str, rows: List[Tuple[str, str]]):
        story.append(Paragraph(title, styles["SectionTitle"]))
        data = [["Field", "Value"]]
        for k, v in rows:
            data.append([str(k), str(v if v is not None else "N/A")])

        table = Table(data, colWidths=[65 * mm, 115 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF1FF")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F3A8A")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 8))

    def _add_bullet_list(self, story: List[Any], styles, subtitle: str, items: List[str]):
        story.append(Paragraph(f"<b>{subtitle}</b>", styles["Body"]))
        if not items:
            story.append(Paragraph("• Not available", styles["Body"]))
            return
        for item in items[:8]:
            story.append(Paragraph(f"• {item}", styles["Body"]))
        story.append(Spacer(1, 4))

    @staticmethod
    def _extract_financial_metrics(financial: FinancialMetrics | None) -> Dict[str, float]:
        if not financial:
            return {}
        data: Dict[str, Any] = {}
        if isinstance(financial.metrics_json, dict):
            data.update(financial.metrics_json)
        if isinstance(financial.ratios_json, dict):
            data.update(financial.ratios_json)
        return {
            "debt_to_equity": float(data.get("debt_to_equity", 0) or 0),
            "current_ratio": float(data.get("current_ratio", 0) or 0),
            "debt_service_coverage_ratio": float(data.get("debt_service_coverage_ratio", 0) or 0),
            "net_profit_margin": float(data.get("net_profit_margin", 0) or 0),
            "return_on_assets": float(data.get("return_on_assets", 0) or 0),
        }

    @staticmethod
    def _extract_market_sentiment(sentiment: MarketSentiment | None, report: ResearchReport | None) -> Dict[str, Any]:
        if sentiment:
            return {
                "composite_sentiment_score": sentiment.composite_sentiment_score or 0,
                "overall_tone": sentiment.overall_tone or "NEUTRAL",
                "analyst_rating": sentiment.analyst_rating,
                "negative_mentions": sentiment.negative_mentions,
            }
        if report and isinstance(report.executive_summary, dict):
            return report.executive_summary.get("market_sentiment", {})
        return {"composite_sentiment_score": 0, "overall_tone": "NEUTRAL"}

    @staticmethod
    def _extract_industry_data(entity: Entity, industry: IndustryReport | None, report: ResearchReport | None) -> Dict[str, Any]:
        if industry:
            return {
                "industry": industry.industry,
                "growth_rate_cagr": industry.growth_rate_cagr or 0,
                "market_attractiveness": industry.market_attractiveness or "MODERATE",
                "regulatory_environment": industry.regulatory_environment or "NEUTRAL",
            }
        if report and isinstance(report.executive_summary, dict):
            from_report = report.executive_summary.get("industry", {})
            if isinstance(from_report, dict) and from_report:
                return from_report
        return {
            "industry": entity.sector or "General",
            "growth_rate_cagr": 0,
            "market_attractiveness": "MODERATE",
            "regulatory_environment": "NEUTRAL",
        }

    @staticmethod
    def _extract_shareholding_data(financial: FinancialMetrics | None, report: ResearchReport | None) -> List[Tuple[str, str]]:
        share = {}
        if financial and isinstance(financial.metrics_json, dict):
            share = financial.metrics_json.get("shareholding") or {}
        if not share and report and isinstance(report.executive_summary, dict):
            share = report.executive_summary.get("shareholding") or {}

        if isinstance(share, dict) and share:
            rows = []
            for k, v in share.items():
                rows.append((str(k).replace("_", " ").title(), f"{v}%" if isinstance(v, (int, float)) else str(v)))
            return rows

        return [
            ("Promoter Holding", "Data not available"),
            ("Institutional Holding", "Data not available"),
            ("Public Holding", "Data not available"),
            ("Remarks", "Shareholding structure not present in current datasets"),
        ]

    @staticmethod
    def _build_loan_recommendation(entity: Entity,
                                   credit_score: CreditScore | None,
                                   underwriting: UnderwritingDecision | None,
                                   legal_risks: List[LegalRisk]) -> List[Tuple[str, str]]:
        has_high_legal = any((r.severity or "").upper() in {"HIGH", "CRITICAL"} for r in legal_risks)
        score_value = credit_score.credit_score if credit_score and credit_score.credit_score is not None else None

        if underwriting and underwriting.decision:
            decision = underwriting.decision
        elif score_value is None:
            decision = "REVIEW_REQUIRED"
        elif score_value >= 780 and not has_high_legal:
            decision = "APPROVE"
        elif score_value >= 680 and not has_high_legal:
            decision = "APPROVE_WITH_CONDITIONS"
        else:
            decision = "DECLINE_OR_RESTRUCTURE"

        conditions = []
        if has_high_legal:
            conditions.append("Resolve high-severity legal/regulatory issues before disbursement")
        if entity.loan_amount and credit_score and score_value and score_value < 700:
            conditions.append("Consider collateral enhancement for requested exposure")
        if entity.tenure and entity.tenure > 60:
            conditions.append("Review long tenor risk with periodic covenant checks")
        if not conditions:
            conditions.append("Standard covenants and annual review are adequate")

        return [
            ("Recommended Decision", decision),
            ("Requested Amount", CAMReportGenerator._fmt_inr(entity.loan_amount)),
            ("Suggested Rate Guidance", f"{underwriting.proposed_interest_rate:.2f}%" if underwriting and underwriting.proposed_interest_rate else "As per risk-based pricing grid"),
            ("Key Conditions", "; ".join(conditions)),
            ("Rationale", "Recommendation is based on quantitative score, legal posture, and explainable risk drivers"),
        ]

    @staticmethod
    def _fmt_num(value: Any) -> str:
        if value is None or value == "":
            return "N/A"
        try:
            return f"{float(value):,.2f}"
        except Exception:
            return str(value)

    @staticmethod
    def _fmt_pct(value: Any) -> str:
        if value is None or value == "":
            return "N/A"
        try:
            return f"{float(value) * 100:.2f}%"
        except Exception:
            return str(value)

    @staticmethod
    def _fmt_inr(value: Any) -> str:
        if value is None or value == "":
            return "N/A"
        try:
            return f"INR {float(value):,.2f}"
        except Exception:
            return str(value)
