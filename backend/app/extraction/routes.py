"""Routes for extraction review: GET results and POST approval."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.extraction.models import ExtractionResult
from app.extraction.schemas import (
    ApproveExtractionRequest,
    ApproveExtractionResponse,
    ExtractedField,
    ExtractionResultResponse,
    ExtractionSection,
)
from app.metrics.models import FinancialMetrics
from app.models.entity import Entity
from app.utils.security import decode_token

router = APIRouter(prefix="/extraction", tags=["extraction-review"])
security = HTTPBearer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SECTION_META: Dict[str, Dict[str, Any]] = {
    "balance_sheet": {
        "label": "Balance Sheet",
        "fields": {
            "total_assets": ("Total Assets", "INR"),
            "total_liabilities": ("Total Liabilities", "INR"),
            "current_assets": ("Current Assets", "INR"),
            "current_liabilities": ("Current Liabilities", "INR"),
            "equity": ("Shareholder Equity", "INR"),
            "cash_and_equivalents": ("Cash & Equivalents", "INR"),
            "inventory": ("Inventory", "INR"),
            "accounts_receivable": ("Accounts Receivable", "INR"),
            "fixed_assets": ("Fixed Assets / PPE", "INR"),
            "long_term_debt": ("Long-term Debt", "INR"),
        },
    },
    "income_statement": {
        "label": "Income Statement",
        "fields": {
            "revenue": ("Revenue / Turnover", "INR"),
            "gross_profit": ("Gross Profit", "INR"),
            "ebitda": ("EBITDA", "INR"),
            "ebit": ("EBIT", "INR"),
            "net_profit": ("Net Profit / PAT", "INR"),
            "interest_expense": ("Interest Expense", "INR"),
            "depreciation": ("Depreciation", "INR"),
            "tax": ("Income Tax", "INR"),
            "operating_expenses": ("Operating Expenses", "INR"),
        },
    },
    "cash_flow": {
        "label": "Cash Flow",
        "fields": {
            "operating_cash_flow": ("Operating Cash Flow", "INR"),
            "investing_cash_flow": ("Investing Cash Flow", "INR"),
            "financing_cash_flow": ("Financing Cash Flow", "INR"),
            "free_cash_flow": ("Free Cash Flow", "INR"),
            "capex": ("Capital Expenditure", "INR"),
        },
    },
    "financial_ratios": {
        "label": "Financial Ratios",
        "fields": {
            "current_ratio": ("Current Ratio", "x"),
            "quick_ratio": ("Quick Ratio", "x"),
            "debt_to_equity": ("Debt-to-Equity Ratio", "x"),
            "interest_coverage": ("Interest Coverage Ratio", "x"),
            "dscr": ("DSCR", "x"),
            "roe": ("Return on Equity (ROE)", "%"),
            "roa": ("Return on Assets (ROA)", "%"),
            "net_margin": ("Net Profit Margin", "%"),
            "gross_margin": ("Gross Profit Margin", "%"),
            "asset_turnover": ("Asset Turnover", "x"),
        },
    },
    "credit_inputs": {
        "label": "Credit Score Inputs",
        "fields": {
            "financial_score": ("Financial Score", "pts"),
            "liquidity_score": ("Liquidity Score", "pts"),
            "profitability_score": ("Profitability Score", "pts"),
            "solvency_score": ("Solvency Score", "pts"),
            "efficiency_score": ("Efficiency Score", "pts"),
            "overall_health_score": ("Overall Health Score", "pts"),
        },
    },
}


def _safe_float(v: Any) -> Optional[float]:
    """Convert value to float, return None on failure."""
    try:
        f = float(v)
        return None if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return None


def _build_extracted_fields(metrics: FinancialMetrics) -> Dict[str, Dict[str, ExtractedField]]:
    """Build the section→field structure from a FinancialMetrics row."""
    raw_metrics: Dict = metrics.metrics_json or {}
    raw_ratios: Dict = metrics.ratios_json or {}
    raw_credit: Dict = metrics.credit_score_inputs_json or {}

    # Flatten all source data
    sources: Dict[str, Dict] = {
        "balance_sheet": {**raw_metrics.get("balance_sheet", {}), **raw_metrics},
        "income_statement": {**raw_metrics.get("income_statement", {}), **raw_metrics},
        "cash_flow": {**raw_metrics.get("cash_flow", {}), **raw_metrics},
        "financial_ratios": raw_ratios,
        "credit_inputs": {
            "financial_score": _safe_float(metrics.profitability_score),
            "liquidity_score": _safe_float(metrics.liquidity_score),
            "profitability_score": _safe_float(metrics.profitability_score),
            "solvency_score": _safe_float(metrics.solvency_score),
            "efficiency_score": _safe_float(metrics.efficiency_score),
            "overall_health_score": _safe_float(metrics.overall_health_score),
            **raw_credit,
        },
    }

    result: Dict[str, Dict[str, ExtractedField]] = {}

    for section_key, smeta in SECTION_META.items():
        src = sources.get(section_key, {})
        fields: Dict[str, ExtractedField] = {}
        for field_key, (label, unit) in smeta["fields"].items():
            # try multiple key variants
            raw_val = src.get(field_key) or src.get(field_key.replace("_", " "))
            value = _safe_float(raw_val) if raw_val is not None else None
            confidence = 0.90 if value is not None else 0.0
            fields[field_key] = ExtractedField(
                value=value,
                label=label,
                unit=unit,
                confidence=confidence,
                source=f"financial_metrics#{metrics.id}",
            )
        result[section_key] = fields

    return result


def _build_sections(
    extracted: Dict[str, Dict[str, ExtractedField]],
) -> List[ExtractionSection]:
    sections = []
    for section_key, smeta in SECTION_META.items():
        fields = extracted.get(section_key, {})
        confidences = [f.confidence for f in fields.values() if f.confidence > 0]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        sections.append(
            ExtractionSection(
                section_key=section_key,
                section_label=smeta["label"],
                fields=fields,
                average_confidence=round(avg_conf, 4),
            )
        )
    return sections


def _overall_confidence(sections: List[ExtractionSection]) -> float:
    vals = [s.average_confidence for s in sections if s.average_confidence > 0]
    return round(sum(vals) / len(vals), 4) if vals else 0.0


def _total_fields(sections: List[ExtractionSection]) -> int:
    return sum(len([f for f in s.fields.values() if f.value is not None]) for s in sections)


def _count_populated_extracted_fields(raw_extracted: Dict[str, Any]) -> int:
    if not isinstance(raw_extracted, dict):
        return 0

    count = 0
    for section_key in ["company_info", "income_statement", "balance_sheet", "cash_flow"]:
        section = raw_extracted.get(section_key, {})
        if not isinstance(section, dict):
            continue
        for value in section.values():
            if value is not None and value != "":
                count += 1
    return count


def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> int:
    payload = decode_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return int(payload.get("sub"))


# ---------------------------------------------------------------------------
# GET /extraction/results/{entity_id}
# ---------------------------------------------------------------------------

@router.get("/results/{entity_id}", response_model=ExtractionResultResponse)
def get_extraction_results(
    entity_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Return extraction results for an entity.

    First looks for an existing ExtractionResult row (latest). If none exists,
    synthesises one from the most recent FinancialMetrics record and persists it.
    """
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    # 1. Try existing ExtractionResult
    existing_results: List[ExtractionResult] = (
        db.query(ExtractionResult)
        .filter(ExtractionResult.entity_id == entity_id)
        .order_by(ExtractionResult.created_at.desc())
        .limit(20)
        .all()
    )

    existing: Optional[ExtractionResult] = None
    if existing_results:
        best = sorted(
            existing_results,
            key=lambda row: (
                _count_populated_extracted_fields(row.extracted_fields or {}),
                row.created_at,
            ),
            reverse=True,
        )[0]
        existing = best

    if existing:
        # Re-hydrate ExtractedField objects from stored JSON
        raw_extracted: Dict = existing.extracted_fields or {}
        sections_data: Dict[str, Dict[str, ExtractedField]] = {}
        for sec_key, field_dict in raw_extracted.items():
            if not isinstance(field_dict, dict):
                continue

            section_fields = SECTION_META.get(sec_key, {}).get("fields", {})
            hydrated_fields: Dict[str, ExtractedField] = {}

            for fk, fv in field_dict.items():
                if isinstance(fv, dict):
                    hydrated_fields[fk] = ExtractedField(**fv)
                    continue

                default_label, default_unit = section_fields.get(fk, (fk.replace("_", " ").title(), None))
                hydrated_fields[fk] = ExtractedField(
                    value=_safe_float(fv) if fv is not None else None,
                    label=default_label,
                    unit=default_unit,
                    confidence=0.9 if fv is not None else 0.0,
                )

            sections_data[sec_key] = hydrated_fields

        sections = _build_sections(sections_data)

        return ExtractionResultResponse(
            entity_id=entity_id,
            entity_name=entity.company_name,
            result_id=existing.id,
            document_id=existing.document_id,
            status=existing.status,
            sections=sections,
            corrected_fields=existing.corrected_fields,
            review_notes=existing.review_notes,
            reviewed_at=existing.reviewed_at,
            overall_confidence=_overall_confidence(sections),
            total_fields=_total_fields(sections),
            created_at=existing.created_at,
        )

    # 2. Synthesise from FinancialMetrics
    metrics: Optional[FinancialMetrics] = (
        db.query(FinancialMetrics)
        .filter(FinancialMetrics.entity_id == entity_id)
        .order_by(FinancialMetrics.calculated_at.desc())
        .first()
    )

    if not metrics:
        # Return empty placeholder so the frontend can still render
        empty_sections = [
            ExtractionSection(
                section_key=k,
                section_label=v["label"],
                fields={
                    fk: ExtractedField(value=None, label=fl, unit=fu, confidence=0.0)
                    for fk, (fl, fu) in v["fields"].items()
                },
                average_confidence=0.0,
            )
            for k, v in SECTION_META.items()
        ]
        return ExtractionResultResponse(
            entity_id=entity_id,
            entity_name=entity.company_name,
            result_id=None,
            document_id=None,
            status="pending",
            sections=empty_sections,
            overall_confidence=0.0,
            total_fields=0,
        )

    extracted = _build_extracted_fields(metrics)
    sections = _build_sections(extracted)

    # Convert ExtractedField objects to dict for JSON storage
    extracted_as_dict = {
        sec_key: {fk: fv.model_dump() for fk, fv in fields.items()}
        for sec_key, fields in extracted.items()
    }

    new_result = ExtractionResult(
        entity_id=entity_id,
        document_id=metrics.document_id,
        metrics_id=metrics.id,
        extracted_fields=extracted_as_dict,
        status="pending",
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return ExtractionResultResponse(
        entity_id=entity_id,
        entity_name=entity.company_name,
        result_id=new_result.id,
        document_id=new_result.document_id,
        status=new_result.status,
        sections=sections,
        overall_confidence=_overall_confidence(sections),
        total_fields=_total_fields(sections),
        created_at=new_result.created_at,
    )


# ---------------------------------------------------------------------------
# POST /extraction/approve
# ---------------------------------------------------------------------------

@router.post("/approve", response_model=ApproveExtractionResponse)
def approve_extraction(
    payload: ApproveExtractionRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Save human corrections and mark extraction as approved (or rejected).

    If result_id is provided, updates that row. Otherwise finds the latest
    pending ExtractionResult for the entity.
    """
    # Resolve the target row
    if payload.result_id:
        result = db.query(ExtractionResult).filter(ExtractionResult.id == payload.result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail=f"ExtractionResult {payload.result_id} not found")
    else:
        result = (
            db.query(ExtractionResult)
            .filter(
                ExtractionResult.entity_id == payload.entity_id,
                ExtractionResult.status == "pending",
            )
            .order_by(ExtractionResult.created_at.desc())
            .first()
        )

    now = datetime.utcnow()

    if result:
        result.corrected_fields = payload.corrected_fields
        result.review_notes = payload.review_notes
        result.status = payload.status
        result.reviewed_by = user_id
        result.reviewed_at = now
        result.updated_at = now
        db.commit()
        db.refresh(result)
        result_id = result.id
    else:
        # No existing record – create one representing the review directly
        new_result = ExtractionResult(
            entity_id=payload.entity_id,
            extracted_fields={},
            corrected_fields=payload.corrected_fields,
            review_notes=payload.review_notes,
            status=payload.status,
            reviewed_by=user_id,
            reviewed_at=now,
        )
        db.add(new_result)
        db.commit()
        db.refresh(new_result)
        result_id = new_result.id

    # Count how many fields were corrected
    fields_corrected = sum(
        len(field_dict) for field_dict in payload.corrected_fields.values()
    )

    return ApproveExtractionResponse(
        success=True,
        result_id=result_id,
        entity_id=payload.entity_id,
        status=payload.status,
        fields_corrected=fields_corrected,
        reviewed_at=now,
        message=f"Extraction {payload.status} — {fields_corrected} field(s) corrected.",
    )
