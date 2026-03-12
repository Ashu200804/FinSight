from typing import Dict, Any, List, Optional, Tuple
import re


class FinancialSchemaMapper:
    """Stage 5: schema mapping with table-aware, alias-driven extraction."""

    FIELD_ALIASES = {
        "income_statement": {
            "revenue": ["revenue", "sales", "turnover", "total income"],
            "gross_profit": ["gross profit"],
            "ebitda": ["ebitda"],
            "ebit": ["ebit", "operating profit"],
            "operating_expenses": ["operating expenses", "opex"],
            "interest_expense": ["interest expense", "finance cost", "interest"],
            "tax_expense": ["tax expense", "income tax", "tax"],
            "net_income": ["net income", "net profit", "profit after tax", "pat"],
            "cost_of_goods_sold": ["cost of goods sold", "cogs", "cost of sales"],
        },
        "balance_sheet": {
            "total_assets": ["total assets", "assets"],
            "current_assets": ["current assets"],
            "fixed_assets": ["fixed assets", "ppe", "property plant equipment"],
            "total_liabilities": ["total liabilities", "liabilities"],
            "current_liabilities": ["current liabilities"],
            "long_term_debt": ["long term debt", "long-term debt", "term loan"],
            "short_term_debt": ["short term debt", "short-term debt", "working capital"],
            "total_equity": ["total equity", "equity", "net worth", "shareholders equity"],
            "cash_and_equivalents": ["cash and equivalents", "cash"],
            "accounts_receivable": ["accounts receivable", "trade receivables", "receivables"],
            "inventories": ["inventories", "inventory", "stock"],
        },
        "cash_flow": {
            "operating_cash_flow": ["operating cash flow", "cash from operations"],
            "investing_cash_flow": ["investing cash flow", "cash from investing"],
            "financing_cash_flow": ["financing cash flow", "cash from financing"],
            "capital_expenditure": ["capital expenditure", "capex"],
            "net_cash_flow": ["net cash flow"],
        },
    }

    @staticmethod
    def map_schema(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        mapped_data = {
            "company_info": {
                "company_name": None,
                "cin": None,
                "pan": None,
                "financial_year": None,
            },
            "income_statement": {},
            "balance_sheet": {},
            "cash_flow": {},
            "extracted_fields": [],
        }

        text_lines = FinancialSchemaMapper._collect_text_lines(extracted_data)
        candidates = FinancialSchemaMapper._collect_numeric_candidates(extracted_data, text_lines)

        company_info = FinancialSchemaMapper._extract_company_info(text_lines)
        mapped_data["company_info"].update(company_info)

        extracted_fields: List[str] = []
        for section_key, section_aliases in FinancialSchemaMapper.FIELD_ALIASES.items():
            section_values = {}
            for target_field, aliases in section_aliases.items():
                value = FinancialSchemaMapper._resolve_field_value(candidates, aliases)
                if value is not None:
                    section_values[target_field] = value
                    extracted_fields.append(f"{section_key}.{target_field}")

            mapped_data[section_key] = section_values

        if "total_equity" in mapped_data["balance_sheet"] and "equity" not in mapped_data["balance_sheet"]:
            mapped_data["balance_sheet"]["equity"] = mapped_data["balance_sheet"]["total_equity"]

        mapped_data["extracted_fields"] = extracted_fields
        return mapped_data

    @staticmethod
    def _collect_text_lines(data: Dict[str, Any]) -> List[str]:
        lines: List[str] = []

        ocr_text = data.get("ocr_text")
        if isinstance(ocr_text, str) and ocr_text.strip():
            lines.extend([line.strip() for line in ocr_text.splitlines() if line.strip()])

        ocr_blocks = data.get("ocr_blocks", [])
        if isinstance(ocr_blocks, list):
            for block in ocr_blocks:
                text_value = block.get("text") if isinstance(block, dict) else None
                if isinstance(text_value, str) and text_value.strip():
                    lines.append(text_value.strip())

        for table in data.get("tables", []) or []:
            rows = table.get("data", []) if isinstance(table, dict) else []
            if isinstance(rows, list):
                for row in rows:
                    if isinstance(row, list):
                        serialized = " | ".join(str(cell).strip() for cell in row if str(cell).strip())
                        if serialized:
                            lines.append(serialized)

        return lines

    @staticmethod
    def _collect_numeric_candidates(data: Dict[str, Any], text_lines: List[str]) -> List[Tuple[str, float, int]]:
        candidates: List[Tuple[str, float, int]] = []

        for table in data.get("tables", []) or []:
            rows = table.get("data", []) if isinstance(table, dict) else []
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, list) or not row:
                    continue
                label = str(row[0]).strip().lower()
                if not label:
                    continue
                numeric_values = [FinancialSchemaMapper._parse_number(cell) for cell in row[1:]]
                numeric_values = [value for value in numeric_values if value is not None]
                if numeric_values:
                    candidates.append((label, numeric_values[0], 100))

        for line in text_lines:
            label, value = FinancialSchemaMapper._parse_line_label_value(line)
            if label and value is not None:
                candidates.append((label, value, 60))

        return candidates

    @staticmethod
    def _extract_company_info(lines: List[str]) -> Dict[str, Optional[str]]:
        company_name = None
        cin = None
        pan = None
        financial_year = None

        cin_pattern = re.compile(r"\b[A-Z]{1}[0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}\b", re.IGNORECASE)
        pan_pattern = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
        fy_pattern = re.compile(r"\b(?:FY\s*)?(20\d{2}\s*[-/]\s*20\d{2}|20\d{2})\b", re.IGNORECASE)

        for line in lines:
            if not company_name:
                if "limited" in line.lower() or "ltd" in line.lower() or "tata powers" in line.lower():
                    company_name = line.strip()

            if not cin:
                cin_match = cin_pattern.search(line)
                if cin_match:
                    cin = cin_match.group(0).upper()

            if not pan:
                pan_match = pan_pattern.search(line)
                if pan_match:
                    pan = pan_match.group(0).upper()

            if not financial_year:
                fy_match = fy_pattern.search(line)
                if fy_match:
                    financial_year = fy_match.group(1).replace(" ", "")

        return {
            "company_name": company_name,
            "cin": cin,
            "pan": pan,
            "financial_year": financial_year,
        }

    @staticmethod
    def _resolve_field_value(candidates: List[Tuple[str, float, int]], aliases: List[str]) -> Optional[float]:
        best: Optional[Tuple[float, int]] = None
        normalized_aliases = [alias.lower().strip() for alias in aliases]

        for label, value, source_weight in candidates:
            label_norm = label.lower().strip()
            score = 0
            for alias in normalized_aliases:
                if label_norm == alias:
                    score = max(score, 100)
                elif alias in label_norm:
                    score = max(score, 80)
                elif label_norm in alias:
                    score = max(score, 70)

            if score == 0:
                continue

            total_score = score + source_weight
            if best is None or total_score > best[1]:
                best = (value, total_score)

        return best[0] if best else None

    @staticmethod
    def _parse_line_label_value(line: str) -> Tuple[Optional[str], Optional[float]]:
        cleaned = " ".join(line.replace("\t", " ").split())
        if not cleaned:
            return None, None

        if "|" in cleaned:
            parts = [part.strip() for part in cleaned.split("|") if part.strip()]
            if len(parts) >= 2:
                label = parts[0].lower()
                for part in parts[1:]:
                    parsed = FinancialSchemaMapper._parse_number(part)
                    if parsed is not None:
                        return label, parsed

        separators = [":", "-"]
        for sep in separators:
            if sep in cleaned:
                left, right = cleaned.split(sep, 1)
                parsed = FinancialSchemaMapper._parse_number(right)
                if parsed is not None:
                    return left.strip().lower(), parsed

        number_match = re.search(r"(-?\(?\d[\d,\.]*\)?\s*(?:cr|crore|lakh|lac|million|mn|bn|billion)?)", cleaned, re.IGNORECASE)
        if number_match:
            label = cleaned[:number_match.start()].strip().lower()
            parsed = FinancialSchemaMapper._parse_number(number_match.group(1))
            return (label or None), parsed

        return None, None

    @staticmethod
    def _parse_number(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return None

        lowered = text.lower()
        multiplier = 1.0
        if any(token in lowered for token in ["crore", " cr", "cr "]):
            multiplier = 10_000_000.0
        elif any(token in lowered for token in ["lakh", "lac", " lk", "l "]):
            multiplier = 100_000.0
        elif any(token in lowered for token in ["billion", " bn", "bn "]):
            multiplier = 1_000_000_000.0
        elif any(token in lowered for token in ["million", " mn", "mn "]):
            multiplier = 1_000_000.0

        numeric = re.sub(r"[^0-9.()\-]", "", text)
        if not numeric:
            return None

        is_negative = numeric.startswith("(") and numeric.endswith(")")
        numeric = numeric.replace("(", "").replace(")", "")

        try:
            parsed = float(numeric)
            if is_negative:
                parsed = -parsed
            return parsed * multiplier
        except Exception:
            return None
