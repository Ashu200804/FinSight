import json
import os
import re
from typing import Any, Dict

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class AIStructurer:
    """LLM-assisted structuring stage with deterministic schema guardrails."""

    ALLOWED_SCHEMA = {
        "company_info": ["company_name", "cin", "pan", "financial_year"],
        "income_statement": [
            "revenue", "gross_profit", "ebitda", "ebit", "operating_expenses",
            "interest_expense", "tax_expense", "net_income", "cost_of_goods_sold"
        ],
        "balance_sheet": [
            "total_assets", "current_assets", "fixed_assets", "total_liabilities",
            "current_liabilities", "long_term_debt", "short_term_debt", "total_equity",
            "equity", "cash_and_equivalents", "accounts_receivable", "inventories"
        ],
        "cash_flow": [
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "capital_expenditure", "net_cash_flow"
        ],
    }

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or "ollama"
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("OPENAI_STRUCTURING_MODEL", "gpt-4o-mini")
        self.client = None
        if OpenAI is not None:
            try:
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self.client = OpenAI(**client_kwargs)
            except Exception:
                self.client = None

    def structure_financial_data(self, raw_payload: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
        response = {
            "structured_data": baseline,
            "used_ai": False,
            "confidence": 0.0,
            "warnings": [],
        }

        if not self.client:
            response["warnings"].append("AI structuring skipped (OpenAI client unavailable)")
            return response

        try:
            prompt_payload = {
                "ocr_text": (raw_payload.get("ocr_text") or "")[:12000],
                "ocr_blocks": (raw_payload.get("ocr_blocks") or [])[:120],
                "tables": (raw_payload.get("tables") or [])[:8],
                "baseline": baseline,
                "target_schema": self.ALLOWED_SCHEMA,
            }

            system_prompt = (
                "You are a financial statement structuring engine. "
                "Return only valid JSON. Fill values from OCR/tables into target_schema fields. "
                "Use null when value is unknown. Keep numeric fields as numbers, not strings."
            )

            user_prompt = (
                "Convert this extracted payload into the target financial schema. "
                "Output JSON with keys: company_info, income_statement, balance_sheet, cash_flow.\n"
                f"INPUT={json.dumps(prompt_payload, default=str)}"
            )

            completion = self._create_completion(system_prompt, user_prompt)

            content = completion.choices[0].message.content if completion.choices else None
            if not content:
                response["warnings"].append("AI structuring returned empty content")
                return response

            ai_output = self._safe_json_parse(content)
            if not isinstance(ai_output, dict):
                response["warnings"].append("AI structuring returned non-JSON output")
                return response
            normalized = self._normalize_ai_output(ai_output)
            merged = self._merge_with_baseline(baseline, normalized)

            populated = self._count_populated_fields(merged)
            max_fields = sum(len(v) for v in self.ALLOWED_SCHEMA.values())
            ai_confidence = round(min(1.0, populated / max_fields), 3) if max_fields else 0.0

            response["structured_data"] = merged
            response["used_ai"] = True
            response["confidence"] = ai_confidence
            return response

        except Exception as exc:
            response["warnings"].append(f"AI structuring failed: {str(exc)}")
            return response

    def _create_completion(self, system_prompt: str, user_prompt: str):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            return self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=messages,
            )
        except Exception:
            return self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=messages,
            )

    @staticmethod
    def _safe_json_parse(content: str):
        try:
            return json.loads(content)
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", content or "")
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
        return None

    def _normalize_ai_output(self, ai_output: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {
            "company_info": {},
            "income_statement": {},
            "balance_sheet": {},
            "cash_flow": {},
        }

        for section, fields in self.ALLOWED_SCHEMA.items():
            source_section = ai_output.get(section, {}) if isinstance(ai_output, dict) else {}
            if not isinstance(source_section, dict):
                continue
            for field in fields:
                value = source_section.get(field)
                if section == "company_info":
                    normalized[section][field] = str(value).strip() if value is not None and str(value).strip() else None
                else:
                    normalized[section][field] = self._parse_number(value)

        if normalized["balance_sheet"].get("total_equity") is not None and normalized["balance_sheet"].get("equity") is None:
            normalized["balance_sheet"]["equity"] = normalized["balance_sheet"]["total_equity"]

        return normalized

    def _merge_with_baseline(self, baseline: Dict[str, Any], ai_structured: Dict[str, Any]) -> Dict[str, Any]:
        merged = {
            "company_info": dict((baseline or {}).get("company_info", {})),
            "income_statement": dict((baseline or {}).get("income_statement", {})),
            "balance_sheet": dict((baseline or {}).get("balance_sheet", {})),
            "cash_flow": dict((baseline or {}).get("cash_flow", {})),
            "extracted_fields": list((baseline or {}).get("extracted_fields", [])),
        }

        for section, fields in self.ALLOWED_SCHEMA.items():
            target = merged.setdefault(section, {})
            for field in fields:
                baseline_value = target.get(field)
                ai_value = ai_structured.get(section, {}).get(field)
                if (baseline_value is None or baseline_value == "") and ai_value is not None:
                    target[field] = ai_value
                    field_key = f"{section}.{field}"
                    if field_key not in merged["extracted_fields"]:
                        merged["extracted_fields"].append(field_key)

        return merged

    @staticmethod
    def _count_populated_fields(payload: Dict[str, Any]) -> int:
        count = 0
        for section in ["company_info", "income_statement", "balance_sheet", "cash_flow"]:
            values = payload.get(section, {})
            if isinstance(values, dict):
                count += sum(1 for value in values.values() if value is not None and value != "")
        return count

    @staticmethod
    def _parse_number(value: Any):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return None

        lowered = text.lower()
        multiplier = 1.0
        if "crore" in lowered or " cr" in lowered or lowered.endswith("cr"):
            multiplier = 10_000_000.0
        elif "lakh" in lowered or "lac" in lowered or lowered.endswith("lk"):
            multiplier = 100_000.0
        elif "billion" in lowered or lowered.endswith("bn"):
            multiplier = 1_000_000_000.0
        elif "million" in lowered or lowered.endswith("mn"):
            multiplier = 1_000_000.0

        cleaned = re.sub(r"[^0-9.()\-]", "", text)
        if not cleaned:
            return None

        is_negative = cleaned.startswith("(") and cleaned.endswith(")")
        cleaned = cleaned.replace("(", "").replace(")", "")
        try:
            parsed = float(cleaned)
            if is_negative:
                parsed = -parsed
            return parsed * multiplier
        except Exception:
            return None