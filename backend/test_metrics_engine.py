"""
Financial Metrics Engine - Test and Validation Script

This script demonstrates the financial metrics calculation engine
with sample extracted financial data.
"""

from app.metrics.metrics_engine import FinancialMetricsEngine

# Sample extracted financial data from AI pipeline
SAMPLE_EXTRACTED_DATA = {
    'company_info': {
        'company_name': 'TechCorp India Ltd',
        'cin': 'U72900CH2018PLC123456',
        'pan': 'GIRAOP1234T',
    },
    'income_statement': {
        'revenue': 50000000,  # ₹50 million
        'gross_profit': 15000000,  # ₹15 million
        'ebitda': 12000000,  # ₹12 million
        'ebit': 10000000,  # ₹10 million
        'net_income': 7500000,  # ₹7.5 million
        'total_expenses': 40000000,
        'interest_expense': 1500000,  # ₹15 lakh
        'tax_expense': 2500000,  # ₹25 lakh
    },
    'balance_sheet': {
        'total_assets': 100000000,  # ₹100 million
        'current_assets': 40000000,  # ₹40 million
        'non_current_assets': 60000000,
        'total_liabilities': 50000000,  # ₹50 million
        'current_liabilities': 20000000,  # ₹20 million
        'non_current_liabilities': 30000000,
        'long_term_debt': 25000000,  # ₹25 million
        'short_term_debt': 5000000,  # ₹5 million
        'total_equity': 50000000,  # ₹50 million
        'retained_earnings': 30000000,
        'cash_and_equivalents': 8000000,  # ₹80 lakh
        'inventories': 5000000,  # ₹50 lakh
        'accounts_receivable': 12000000,  # ₹1.2 crore
        'accounts_payable': 8000000,  # ₹80 lakh
    },
    'cash_flow': {
        'operating_cash_flow': 9000000,  # ₹90 lakh
        'investing_cash_flow': -2000000,  # -₹20 lakh (capex)
        'financing_cash_flow': -1000000,  # -₹10 lakh (dividend)
        'capital_expenditure': 2000000,  # ₹20 lakh
    }
}

def test_metrics_engine():
    """Run comprehensive tests on the metrics engine"""
    
    print("=" * 80)
    print("FINANCIAL METRICS ENGINE - TEST SUITE")
    print("=" * 80)
    
    # Initialize engine
    engine = FinancialMetricsEngine()
    print("\n✓ Metrics Engine initialized")
    
    # Test 1: Extract financial metrics
    print("\n" + "=" * 80)
    print("TEST 1: EXTRACT FINANCIAL METRICS")
    print("=" * 80)
    
    metrics = engine.extract_financial_metrics(SAMPLE_EXTRACTED_DATA)
    print(f"\n✓ Extracted {len(metrics)} financial metrics")
    print("\nKey Metrics:")
    print(f"  Revenue: ₹{metrics.get('revenue'):,.0f}")
    print(f"  EBITDA: ₹{metrics.get('ebitda'):,.0f}")
    print(f"  Net Profit: ₹{metrics.get('net_profit'):,.0f}")
    print(f"  Total Assets: ₹{metrics.get('total_assets'):,.0f}")
    print(f"  Total Debt: ₹{metrics.get('total_debt'):,.0f}")
    print(f"  Equity: ₹{metrics.get('equity'):,.0f}")
    print(f"  Operating Cash Flow: ₹{metrics.get('operating_cash_flow'):,.0f}")
    
    # Test 2: Calculate all ratios
    print("\n" + "=" * 80)
    print("TEST 2: CALCULATE FINANCIAL RATIOS")
    print("=" * 80)
    
    ratios = engine.calculate_all_ratios(metrics)
    
    # Display profitability ratios
    print("\nPROFITABILITY RATIOS:")
    for ratio_name, ratio_data in ratios['profitability_ratios'].items():
        if ratio_data.get('status') == 'success':
            value = ratio_data.get('value', 0)
            unit = ratio_data.get('unit', '')
            print(f"  {ratio_name.replace('_', ' ').title()}: {value:.2f}{unit}")
            print(f"    → {ratio_data.get('interpretation', '')}")
        else:
            print(f"  {ratio_name.replace('_', ' ').title()}: N/A")
    
    # Display liquidity ratios
    print("\nLIQUIDITY RATIOS:")
    for ratio_name, ratio_data in ratios['liquidity_ratios'].items():
        if ratio_data.get('status') == 'success':
            value = ratio_data.get('value', 0)
            unit = ratio_data.get('unit', '')
            print(f"  {ratio_name.replace('_', ' ').title()}: {value:.2f}{unit}")
            if ratio_data.get('benchmark'):
                print(f"    Benchmark: {ratio_data['benchmark']}")
        else:
            print(f"  {ratio_name.replace('_', ' ').title()}: N/A")
    
    # Display solvency ratios
    print("\nSOLVENCY RATIOS:")
    for ratio_name, ratio_data in ratios['solvency_ratios'].items():
        if ratio_data.get('status') == 'success':
            value = ratio_data.get('value', 0)
            unit = ratio_data.get('unit', '')
            print(f"  {ratio_name.replace('_', ' ').title()}: {value:.2f}{unit}")
            if ratio_data.get('benchmark'):
                print(f"    Benchmark: {ratio_data['benchmark']}")
            if ratio_data.get('warning'):
                print(f"    ⚠️  {ratio_data['warning']}")
        else:
            print(f"  {ratio_name.replace('_', ' ').title()}: N/A")
    
    # Display efficiency ratios
    print("\nEFFICIENCY RATIOS:")
    for ratio_name, ratio_data in ratios['efficiency_ratios'].items():
        if ratio_data.get('status') == 'success':
            value = ratio_data.get('value', 0)
            unit = ratio_data.get('unit', '')
            print(f"  {ratio_name.replace('_', ' ').title()}: {value:.2f}{unit}")
        else:
            print(f"  {ratio_name.replace('_', ' ').title()}: N/A")
    
    # Test 3: Generate credit score inputs
    print("\n" + "=" * 80)
    print("TEST 3: GENERATE CREDIT SCORE INPUTS")
    print("=" * 80)
    
    credit_inputs = engine.generate_credit_score_inputs(metrics, ratios)
    
    print("\nCREDIT SCORING METRICS:")
    print(f"\n  Profitability Score:")
    print(f"    Score: {credit_inputs['profitability_score']['score']:.1f}/{credit_inputs['profitability_score']['max_score']}")
    print(f"    Assessment: {credit_inputs['profitability_score']['assessment']}")
    
    print(f"\n  Liquidity Score:")
    print(f"    Score: {credit_inputs['liquidity_score']['score']:.1f}/{credit_inputs['liquidity_score']['max_score']}")
    print(f"    Assessment: {credit_inputs['liquidity_score']['assessment']}")
    
    print(f"\n  Solvency Score:")
    print(f"    Score: {credit_inputs['solvency_score']['score']:.1f}/{credit_inputs['solvency_score']['max_score']}")
    print(f"    Assessment: {credit_inputs['solvency_score']['assessment']}")
    
    print(f"\n  Efficiency Score:")
    print(f"    Score: {credit_inputs['efficiency_score']['score']:.1f}/{credit_inputs['efficiency_score']['max_score']}")
    print(f"    Assessment: {credit_inputs['efficiency_score']['assessment']}")
    
    print(f"\n  Cash Flow Health: {credit_inputs['cash_flow_health']['status']}")
    print(f"  Leverage Assessment: {credit_inputs['leverage_assessment']['leverage_level']}")
    print(f"  Risk Level: {credit_inputs['leverage_assessment']['risk_level']}")
    
    # Test 4: Warnings and errors
    print("\n" + "=" * 80)
    print("TEST 4: WARNINGS AND ERRORS")
    print("=" * 80)
    
    if engine.warnings:
        print("\nWarnings:")
        for warning in engine.warnings:
            print(f"  ⚠️  {warning}")
    else:
        print("\n✓ No warnings")
    
    if engine.errors:
        print("\nErrors:")
        for error in engine.errors:
            print(f"  ❌ {error}")
    else:
        print("✓ No errors")
    
    # Test 5: Overall health calculation
    print("\n" + "=" * 80)
    print("TEST 5: OVERALL FINANCIAL HEALTH")
    print("=" * 80)
    
    overall_score = (
        credit_inputs['profitability_score']['score'] * 0.3 +
        credit_inputs['liquidity_score']['score'] * 0.25 +
        credit_inputs['solvency_score']['score'] * 0.25 +
        credit_inputs['efficiency_score']['score'] * 0.2
    )
    
    print(f"\nOverall Health Score: {overall_score:.1f}/100")
    if overall_score >= 80:
        rating = "EXCELLENT"
    elif overall_score >= 60:
        rating = "GOOD"
    elif overall_score >= 40:
        rating = "FAIR"
    elif overall_score >= 20:
        rating = "POOR"
    else:
        rating = "VERY POOR"
    
    print(f"Rating: {rating}")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    test_metrics_engine()
