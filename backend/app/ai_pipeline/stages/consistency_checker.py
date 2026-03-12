from typing import Dict, Any, List, Tuple

class FinancialConsistencyChecker:
    """Stage 7: Financial consistency checks"""
    
    @staticmethod
    def run_consistency_checks(financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run comprehensive financial consistency checks
        
        Returns:
        {
            "passed": bool,
            "checks": [
                {
                    "check_name": str,
                    "status": "pass" | "fail" | "warning",
                    "message": str,
                    "severity": "critical" | "high" | "medium" | "low"
                }
            ],
            "summary": {
                "total_checks": int,
                "passed": int,
                "failed": int,
                "warnings": int
            }
        }
        """
        checks = []
        
        bs = financial_data.get("balance_sheet", {})
        income = financial_data.get("income_statement", {})
        
        # Check 1: Balance Sheet equation (Assets = Liabilities + Equity)
        assets = bs.get("total_assets", 0)
        liabilities = bs.get("total_liabilities", 0)
        equity = bs.get("equity", 0)
        
        if assets and (liabilities or equity):
            expected_assets = liabilities + equity
            difference = abs(assets - expected_assets)
            tolerance = assets * 0.05  # 5% tolerance
            
            if difference <= tolerance:
                checks.append({
                    "check_name": "Balance Sheet Equation (A = L + E)",
                    "status": "pass",
                    "message": f"Assets ({assets}) ≈ Liabilities ({liabilities}) + Equity ({equity})",
                    "severity": "critical"
                })
            else:
                checks.append({
                    "check_name": "Balance Sheet Equation (A = L + E)",
                    "status": "fail",
                    "message": f"Imbalance: Difference = {difference} (>{tolerance})",
                    "severity": "critical"
                })
        
        # Check 2: Current assets >= Current liabilities (Liquidity)
        current_assets = bs.get("current_assets", 0)
        current_liabilities = bs.get("current_liabilities", 0)
        
        if current_assets and current_liabilities:
            if current_assets >= current_liabilities:
                checks.append({
                    "check_name": "Liquidity Check (CA >= CL)",
                    "status": "pass",
                    "message": f"Current Assets ({current_assets}) >= Current Liabilities ({current_liabilities})",
                    "severity": "high"
                })
            else:
                checks.append({
                    "check_name": "Liquidity Check (CA >= CL)",
                    "status": "warning",
                    "message": f"Negative working capital: CA ({current_assets}) < CL ({current_liabilities})",
                    "severity": "high"
                })
        
        # Check 3: Income statement flows to retained earnings
        net_income = income.get("net_income", 0)
        revenue = income.get("revenue", 0)
        
        if revenue:
            profit_margin = (net_income / revenue) * 100 if revenue else 0
            
            if 0 <= profit_margin <= 50:
                checks.append({
                    "check_name": "Profit Margin Reasonableness",
                    "status": "pass",
                    "message": f"Profit margin: {profit_margin:.2f}% (reasonable range)",
                    "severity": "medium"
                })
            else:
                checks.append({
                    "check_name": "Profit Margin Reasonableness",
                    "status": "warning",
                    "message": f"Profit margin: {profit_margin:.2f}% (unusual)",
                    "severity": "medium"
                })
        
        # Check 4: Revenue consistency
        gross_profit = income.get("gross_profit", 0)
        cogs = income.get("cost_of_goods_sold", 0)
        
        if gross_profit and revenue and cogs:
            expected_gross = revenue - cogs
            if abs(gross_profit - expected_gross) < expected_gross * 0.05:
                checks.append({
                    "check_name": "Gross Profit Consistency",
                    "status": "pass",
                    "message": "Gross Profit = Revenue - COGS (consistent)",
                    "severity": "medium"
                })
            else:
                checks.append({
                    "check_name": "Gross Profit Consistency",
                    "status": "fail",
                    "message": "Gross Profit ≠ Revenue - COGS",
                    "severity": "high"
                })
        
        # Check 5: Equity sign check
        if equity and equity < 0:
            checks.append({
                "check_name": "Negative Equity Check",
                "status": "fail",
                "message": f"Negative equity ({equity}) indicates insolvency",
                "severity": "critical"
            })
        
        # Check 6: Liability to Asset ratio
        if assets and liabilities:
            debt_ratio = (liabilities / assets) * 100
            if debt_ratio <= 70:
                checks.append({
                    "check_name": "Debt to Asset Ratio",
                    "status": "pass",
                    "message": f"Debt ratio: {debt_ratio:.2f}% (acceptable)",
                    "severity": "medium"
                })
            else:
                checks.append({
                    "check_name": "Debt to Asset Ratio",
                    "status": "warning",
                    "message": f"High debt ratio: {debt_ratio:.2f}%",
                    "severity": "medium"
                })
        
        # Summary
        passed = sum(1 for c in checks if c["status"] == "pass")
        failed = sum(1 for c in checks if c["status"] == "fail")
        warnings = sum(1 for c in checks if c["status"] == "warning")
        
        overall_passed = failed == 0
        
        return {
            "passed": overall_passed,
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "passed": passed,
                "failed": failed,
                "warnings": warnings
            }
        }
