import json
from typing import Any, Dict, List

import requests

BASE_URL = "http://127.0.0.1:9052"
EMAIL = "analyst@example.com"
PASSWORD = "Password123!"
TARGET_DOC_TYPES = {
    "ALM",
    "Shareholding Pattern",
    "Borrowing Profile",
    "Annual Reports",
    "Portfolio Performance",
}


def count_coverage(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    sections = ["company_info", "income_statement", "balance_sheet", "cash_flow"]
    populated = 0
    total = 0

    for section in sections:
        values = extracted_data.get(section, {}) if isinstance(extracted_data, dict) else {}
        if isinstance(values, dict):
            total += len(values)
            populated += sum(1 for value in values.values() if value not in (None, ""))

    return {
        "populated": populated,
        "total": total,
        "ratio": round((populated / total), 3) if total else 0.0,
    }


def get_latest_entity_id(headers: Dict[str, str]) -> int:
    response = requests.get(f"{BASE_URL}/entity/latest", headers=headers, timeout=30)
    response.raise_for_status()
    return int(response.json().get("id"))


def get_tata_documents(headers: Dict[str, str], entity_id: int) -> List[Dict[str, Any]]:
    response = requests.get(f"{BASE_URL}/documents/entity/{entity_id}", headers=headers, timeout=30)
    response.raise_for_status()
    docs = response.json().get("documents", [])
    return [
        doc for doc in docs
        if str(doc.get("document_type", "")) in TARGET_DOC_TYPES
        or str(doc.get("file_name", "")).endswith(".pdf")
    ]


def main() -> None:
    login = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=30,
    )
    login.raise_for_status()
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    entity_id = get_latest_entity_id(headers)
    documents = get_tata_documents(headers, entity_id)
    output = {"entity_id": entity_id, "documents_found": len(documents), "results": []}

    for doc in documents:
        doc_id = doc.get("id")
        file_name = doc.get("file_name")
        document_type = doc.get("document_type")
        process_response = requests.get(
            f"{BASE_URL}/ai/extract/process-document/{doc_id}", headers=headers, timeout=240
        )

        process_json = {}
        if process_response.headers.get("content-type", "").startswith("application/json"):
            process_json = process_response.json()

        processing_results = process_json.get("processing_results", {})
        extracted_data = processing_results.get("extracted_data", {})

        metrics_response = requests.post(
            f"{BASE_URL}/api/metrics/calculate",
            headers={**headers, "Content-Type": "application/json"},
            json={"document_id": doc_id, "use_extracted_data": True},
            timeout=240,
        )

        metrics_json = {}
        if metrics_response.headers.get("content-type", "").startswith("application/json"):
            metrics_json = metrics_response.json()

        output["results"].append(
            {
                "document_id": doc_id,
                "file_name": file_name,
                "document_type": document_type,
                "process_status": process_response.status_code,
                "metrics_status": metrics_response.status_code,
                "pipeline_confidence": processing_results.get("overall_confidence"),
                "ai_structuring": processing_results.get("pipeline_stages", {}).get("ai_structuring", {}),
                "coverage": count_coverage(extracted_data),
                "key_fields": {
                    "revenue": (extracted_data.get("income_statement") or {}).get("revenue") if isinstance(extracted_data, dict) else None,
                    "total_assets": (extracted_data.get("balance_sheet") or {}).get("total_assets") if isinstance(extracted_data, dict) else None,
                    "net_income": (extracted_data.get("income_statement") or {}).get("net_income") if isinstance(extracted_data, dict) else None,
                },
                "metrics_summary": {
                    "credit_score": (metrics_json.get("assessment") or {}).get("credit_score"),
                    "recommendation": (metrics_json.get("assessment") or {}).get("recommendation"),
                    "dscr": (((metrics_json.get("ratios") or {}).get("liquidity") or {}).get("debt_service_coverage_ratio")),
                },
            }
        )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
