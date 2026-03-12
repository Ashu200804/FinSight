import csv
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE_DIR = Path("c:/Users/hp/iit_hyderabad_hackathon/mock_data/Tata_Powers")
BASE_DIR.mkdir(parents=True, exist_ok=True)

company_name = "Tata Powers"

mock_docs = {
    "ALM": [
        ["metric", "value", "as_of_date"],
        ["current_assets", "185000000", "2025-03-31"],
        ["current_liabilities", "124000000", "2025-03-31"],
        ["long_term_debt", "255000000", "2025-03-31"],
        ["short_term_debt", "42000000", "2025-03-31"],
        ["cash_and_equivalents", "38000000", "2025-03-31"],
        ["inventory", "9000000", "2025-03-31"],
        ["accounts_receivable", "46000000", "2025-03-31"],
    ],
    "Shareholding_Pattern": [
        ["shareholder_category", "shares", "holding_percent"],
        ["Promoters", "840000000", "43.25"],
        ["FIIs", "390000000", "20.08"],
        ["DIIs", "285000000", "14.67"],
        ["Public", "428000000", "22.00"],
    ],
    "Borrowing_Profile": [
        ["borrowing_type", "principal_outstanding", "interest_rate", "maturity_date"],
        ["Term Loan", "145000000", "8.95", "2030-09-30"],
        ["Working Capital", "42000000", "9.60", "2026-06-30"],
        ["NCD", "68000000", "8.40", "2029-03-31"],
        ["ECB", "50000000", "7.10", "2031-12-31"],
    ],
    "Annual_Reports": [
        ["line_item", "fy_2025", "fy_2024"],
        ["revenue", "465000000", "441000000"],
        ["gross_profit", "186000000", "171000000"],
        ["ebitda", "93500000", "87200000"],
        ["net_income", "31200000", "28600000"],
        ["total_assets", "690000000", "648000000"],
        ["total_liabilities", "462000000", "435000000"],
        ["total_equity", "228000000", "213000000"],
        ["operating_cash_flow", "59800000", "55200000"],
        ["capital_expenditure", "22800000", "20500000"],
    ],
    "Portfolio_Performance": [
        ["portfolio_segment", "capacity_mw", "plf_percent", "revenue_contribution_percent"],
        ["Thermal", "4310", "74.8", "41.2"],
        ["Hydro", "912", "58.1", "12.4"],
        ["Solar", "2875", "24.6", "21.3"],
        ["Wind", "1340", "30.2", "15.8"],
        ["Transmission_Distribution", "NA", "NA", "9.3"],
    ],
}


def write_csv(name, rows):
    csv_path = BASE_DIR / f"{name}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return csv_path


def write_pdf(name, rows):
    pdf_path = BASE_DIR / f"{name}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, company_name)
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Mock Document: {name.replace('_', ' ')}")
    y -= 24

    c.setFont("Helvetica", 9)
    for row in rows:
        line = " | ".join(str(col) for col in row)
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)
        c.drawString(40, y, line[:140])
        y -= 14

    c.save()
    return pdf_path


created = []
for doc_name, data_rows in mock_docs.items():
    created.append(write_csv(doc_name, data_rows))
    created.append(write_pdf(doc_name, data_rows))

print("Created files:")
for p in created:
    print(p)
