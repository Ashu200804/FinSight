from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class MetricStatus(str, Enum):
    """Status of metric calculation"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class FinancialMetricsEngine:
    """
    Production-grade financial metrics engine for B2B credit underwriting.
    Extracts and calculates key financial metrics and ratios.
    """
    
    def __init__(self):
        self.calculated_at = datetime.utcnow()
        self.warnings = []
        self.errors = []
    
    def extract_financial_metrics(self, extracted_data: Dict) -> Dict:
        """
        Extract key financial metrics from AI pipeline output.
        
        Args:
            extracted_data: Output from DocumentExtractionPipeline
            
        Returns:
            Dictionary with extracted metrics and validation status
        """
        try:
            balance_sheet = extracted_data.get('balance_sheet', {})
            income_statement = extracted_data.get('income_statement', {})
            cash_flow = extracted_data.get('cash_flow', {})
            
            metrics = {
                # Income Statement Metrics
                'revenue': self._parse_metric(income_statement.get('revenue')),
                'gross_profit': self._parse_metric(income_statement.get('gross_profit')),
                'ebitda': self._parse_metric(income_statement.get('ebitda')),
                'ebit': self._parse_metric(income_statement.get('ebit')),
                'net_profit': self._parse_metric(income_statement.get('net_income')),
                'total_expenses': self._parse_metric(income_statement.get('total_expenses')),
                'interest_expense': self._parse_metric(income_statement.get('interest_expense')),
                'tax_expense': self._parse_metric(income_statement.get('tax_expense')),
                
                # Balance Sheet Metrics
                'total_assets': self._parse_metric(balance_sheet.get('total_assets')),
                'current_assets': self._parse_metric(balance_sheet.get('current_assets')),
                'non_current_assets': self._parse_metric(balance_sheet.get('non_current_assets')),
                'total_liabilities': self._parse_metric(balance_sheet.get('total_liabilities')),
                'current_liabilities': self._parse_metric(balance_sheet.get('current_liabilities')),
                'non_current_liabilities': self._parse_metric(balance_sheet.get('non_current_liabilities')),
                'total_debt': self._parse_metric(
                    balance_sheet.get('long_term_debt', 0) + balance_sheet.get('short_term_debt', 0)
                ),
                'short_term_debt': self._parse_metric(balance_sheet.get('short_term_debt')),
                'long_term_debt': self._parse_metric(balance_sheet.get('long_term_debt')),
                'equity': self._parse_metric(balance_sheet.get('total_equity')),
                'retained_earnings': self._parse_metric(balance_sheet.get('retained_earnings')),
                'cash_and_equivalents': self._parse_metric(balance_sheet.get('cash_and_equivalents')),
                'inventories': self._parse_metric(balance_sheet.get('inventories')),
                'accounts_receivable': self._parse_metric(balance_sheet.get('accounts_receivable')),
                'accounts_payable': self._parse_metric(balance_sheet.get('accounts_payable')),
                
                # Cash Flow Metrics
                'operating_cash_flow': self._parse_metric(cash_flow.get('operating_cash_flow')),
                'investing_cash_flow': self._parse_metric(cash_flow.get('investing_cash_flow')),
                'financing_cash_flow': self._parse_metric(cash_flow.get('financing_cash_flow')),
                'free_cash_flow': self._parse_metric(
                    (cash_flow.get('operating_cash_flow', 0) or 0) - (cash_flow.get('capital_expenditure', 0) or 0)
                ),
            }
            
            return metrics
        
        except Exception as e:
            self.errors.append(f"Error extracting financial metrics: {str(e)}")
            return {}
    
    def calculate_all_ratios(self, metrics: Dict) -> Dict:
        """
        Calculate all financial ratios from extracted metrics.
        
        Args:
            metrics: Dictionary of financial metrics
            
        Returns:
            Dictionary with calculated ratios and validation status
        """
        ratios = {
            'profitability_ratios': self._calculate_profitability_ratios(metrics),
            'liquidity_ratios': self._calculate_liquidity_ratios(metrics),
            'solvency_ratios': self._calculate_solvency_ratios(metrics),
            'efficiency_ratios': self._calculate_efficiency_ratios(metrics),
            'valuation_ratios': self._calculate_valuation_ratios(metrics),
        }
        
        return ratios
    
    def _calculate_profitability_ratios(self, metrics: Dict) -> Dict:
        """Calculate profitability ratios"""
        ratios = {}
        
        # Profit Margin
        revenue = metrics.get('revenue')
        net_profit = metrics.get('net_profit')
        if revenue and revenue > 0 and net_profit is not None:
            ratios['profit_margin'] = {
                'value': (net_profit / revenue) * 100,
                'unit': '%',
                'interpretation': 'Net profit per rupee of revenue',
                'status': 'success'
            }
        else:
            self.warnings.append("Cannot calculate Profit Margin: Missing or invalid revenue")
            ratios['profit_margin'] = {'status': 'error', 'reason': 'Missing revenue or net profit'}
        
        # Gross Profit Margin
        gross_profit = metrics.get('gross_profit')
        if revenue and revenue > 0 and gross_profit is not None:
            ratios['gross_profit_margin'] = {
                'value': (gross_profit / revenue) * 100,
                'unit': '%',
                'interpretation': 'Gross profit per rupee of revenue',
                'status': 'success'
            }
        else:
            ratios['gross_profit_margin'] = {'status': 'error', 'reason': 'Missing revenue or gross profit'}
        
        # EBITDA Margin
        ebitda = metrics.get('ebitda')
        if revenue and revenue > 0 and ebitda is not None:
            ratios['ebitda_margin'] = {
                'value': (ebitda / revenue) * 100,
                'unit': '%',
                'interpretation': 'EBITDA per rupee of revenue',
                'status': 'success'
            }
        else:
            ratios['ebitda_margin'] = {'status': 'error', 'reason': 'Missing revenue or EBITDA'}
        
        # Return on Assets (ROA)
        total_assets = metrics.get('total_assets')
        if total_assets and total_assets > 0 and net_profit is not None:
            ratios['return_on_assets'] = {
                'value': (net_profit / total_assets) * 100,
                'unit': '%',
                'interpretation': 'Net income generated per rupee of assets',
                'status': 'success',
                'benchmark': '5-10% is typical'
            }
        else:
            ratios['return_on_assets'] = {'status': 'error', 'reason': 'Missing assets or net profit'}
        
        # Return on Equity (ROE)
        equity = metrics.get('equity')
        if equity and equity > 0 and net_profit is not None:
            ratios['return_on_equity'] = {
                'value': (net_profit / equity) * 100,
                'unit': '%',
                'interpretation': 'Net income generated per rupee of equity',
                'status': 'success',
                'benchmark': '10-15% is typical'
            }
        else:
            ratios['return_on_equity'] = {'status': 'error', 'reason': 'Missing equity or net profit'}
        
        return ratios
    
    def _calculate_liquidity_ratios(self, metrics: Dict) -> Dict:
        """Calculate liquidity ratios"""
        ratios = {}
        
        # Current Ratio
        current_assets = metrics.get('current_assets')
        current_liabilities = metrics.get('current_liabilities')
        if current_assets is not None and current_liabilities and current_liabilities > 0:
            ratios['current_ratio'] = {
                'value': current_assets / current_liabilities,
                'unit': 'ratio',
                'interpretation': 'Short-term financial position',
                'status': 'success',
                'benchmark': '1.5-3.0 is healthy',
                'warning': self._check_current_ratio(current_assets / current_liabilities)
            }
        else:
            self.warnings.append("Cannot calculate Current Ratio: Missing current assets or liabilities")
            ratios['current_ratio'] = {'status': 'error', 'reason': 'Missing current assets or liabilities'}
        
        # Quick Ratio (Acid Test)
        inventories = metrics.get('inventories', 0) or 0
        if current_assets is not None and current_liabilities and current_liabilities > 0:
            quick_assets = current_assets - inventories
            ratios['quick_ratio'] = {
                'value': quick_assets / current_liabilities,
                'unit': 'ratio',
                'interpretation': 'Stringent liquidity measure (excluding inventory)',
                'status': 'success',
                'benchmark': '1.0 or higher is healthy'
            }
        else:
            ratios['quick_ratio'] = {'status': 'error', 'reason': 'Missing current assets or liabilities'}
        
        # Cash Ratio
        cash = metrics.get('cash_and_equivalents', 0) or 0
        if current_liabilities and current_liabilities > 0:
            ratios['cash_ratio'] = {
                'value': cash / current_liabilities,
                'unit': 'ratio',
                'interpretation': 'Immediate liquidity (cash only)',
                'status': 'success',
                'benchmark': '0.2-0.5 is typical'
            }
        else:
            ratios['cash_ratio'] = {'status': 'error', 'reason': 'Missing cash or current liabilities'}
        
        # Working Capital
        working_capital = (current_assets or 0) - (current_liabilities or 0)
        ratios['working_capital'] = {
            'value': working_capital,
            'unit': 'currency',
            'interpretation': 'Available capital for short-term operations',
            'status': 'success',
            'warning': 'Negative working capital may indicate liquidity stress' if working_capital < 0 else None
        }
        
        # Working Capital Ratio
        if current_assets and current_liabilities:
            wc_ratio = working_capital / current_liabilities
            ratios['working_capital_ratio'] = {
                'value': wc_ratio,
                'unit': 'ratio',
                'interpretation': 'Working capital as percentage of current liabilities',
                'status': 'success'
            }
        else:
            ratios['working_capital_ratio'] = {'status': 'error', 'reason': 'Missing current assets or liabilities'}
        
        return ratios
    
    def _calculate_solvency_ratios(self, metrics: Dict) -> Dict:
        """Calculate solvency ratios"""
        ratios = {}
        
        # Debt to Equity Ratio
        total_debt = metrics.get('total_debt')
        equity = metrics.get('equity')
        if total_debt is not None and equity and equity > 0:
            ratios['debt_to_equity'] = {
                'value': total_debt / equity,
                'unit': 'ratio',
                'interpretation': 'Proportion of debt and equity used to finance assets',
                'status': 'success',
                'benchmark': '0.5-2.0 is typical',
                'warning': self._check_debt_to_equity(total_debt / equity)
            }
        else:
            self.warnings.append("Cannot calculate Debt to Equity: Missing debt or equity")
            ratios['debt_to_equity'] = {'status': 'error', 'reason': 'Missing debt or equity'}
        
        # Debt to Assets Ratio
        total_assets = metrics.get('total_assets')
        if total_debt is not None and total_assets and total_assets > 0:
            ratios['debt_to_assets'] = {
                'value': (total_debt / total_assets) * 100,
                'unit': '%',
                'interpretation': 'Percentage of assets financed by debt',
                'status': 'success',
                'benchmark': '<60% is typical'
            }
        else:
            ratios['debt_to_assets'] = {'status': 'error', 'reason': 'Missing debt or assets'}
        
        # Equity Ratio
        if equity is not None and total_assets and total_assets > 0:
            ratios['equity_ratio'] = {
                'value': (equity / total_assets) * 100,
                'unit': '%',
                'interpretation': 'Percentage of assets financed by equity',
                'status': 'success'
            }
        else:
            ratios['equity_ratio'] = {'status': 'error', 'reason': 'Missing equity or assets'}
        
        # Interest Coverage Ratio
        ebit = metrics.get('ebit')
        interest_expense = metrics.get('interest_expense')
        if ebit is not None and interest_expense and interest_expense > 0:
            ratios['interest_coverage'] = {
                'value': ebit / interest_expense,
                'unit': 'times',
                'interpretation': 'Ability to cover interest payments from operating income',
                'status': 'success',
                'benchmark': '>2.5x is healthy',
                'warning': self._check_interest_coverage(ebit / interest_expense)
            }
        else:
            self.warnings.append("Cannot calculate Interest Coverage: Missing EBIT or interest expense")
            ratios['interest_coverage'] = {'status': 'error', 'reason': 'Missing EBIT or interest expense'}
        
        # Debt Service Coverage Ratio
        operating_cf = metrics.get('operating_cash_flow')
        if operating_cf is not None and total_debt and total_debt > 0:
            ratios['debt_service_coverage'] = {
                'value': operating_cf / total_debt,
                'unit': 'ratio',
                'interpretation': 'Ability to service debt from operating cash flow',
                'status': 'success',
                'benchmark': '>1.25x is healthy'
            }
        else:
            ratios['debt_service_coverage'] = {'status': 'error', 'reason': 'Missing cash flow or debt'}
        
        return ratios
    
    def _calculate_efficiency_ratios(self, metrics: Dict) -> Dict:
        """Calculate efficiency ratios"""
        ratios = {}
        
        revenue = metrics.get('revenue')
        
        # Asset Turnover
        total_assets = metrics.get('total_assets')
        if revenue and revenue > 0 and total_assets and total_assets > 0:
            ratios['asset_turnover'] = {
                'value': revenue / total_assets,
                'unit': 'times',
                'interpretation': 'Revenue generated per rupee of assets',
                'status': 'success',
                'benchmark': '1.0-2.0 is typical'
            }
        else:
            ratios['asset_turnover'] = {'status': 'error', 'reason': 'Missing revenue or assets'}
        
        # Inventory Turnover
        inventories = metrics.get('inventories')
        cogs = metrics.get('gross_profit') and (revenue - metrics.get('gross_profit')) or revenue
        if inventories and inventories > 0 and cogs:
            ratios['inventory_turnover'] = {
                'value': cogs / inventories,
                'unit': 'times',
                'interpretation': 'Number of times inventory is sold and replaced',
                'status': 'success'
            }
        else:
            ratios['inventory_turnover'] = {'status': 'error', 'reason': 'Missing inventory or COGS'}
        
        # Receivables Turnover
        accounts_receivable = metrics.get('accounts_receivable')
        if revenue and revenue > 0 and accounts_receivable and accounts_receivable > 0:
            ratios['receivables_turnover'] = {
                'value': revenue / accounts_receivable,
                'unit': 'times',
                'interpretation': 'Number of times accounts receivable is collected',
                'status': 'success'
            }
        else:
            ratios['receivables_turnover'] = {'status': 'error', 'reason': 'Missing revenue or receivables'}
        
        # Days Sales Outstanding (DSO)
        if ratios.get('receivables_turnover', {}).get('status') == 'success':
            dso = 365 / ratios['receivables_turnover']['value']
            ratios['days_sales_outstanding'] = {
                'value': dso,
                'unit': 'days',
                'interpretation': 'Average number of days to collect payment',
                'status': 'success'
            }
        else:
            ratios['days_sales_outstanding'] = {'status': 'error', 'reason': 'Depends on receivables turnover'}
        
        return ratios
    
    def _calculate_valuation_ratios(self, metrics: Dict) -> Dict:
        """Calculate valuation and other ratios"""
        ratios = {}
        
        revenue = metrics.get('revenue')
        net_profit = metrics.get('net_profit')
        total_assets = metrics.get('total_assets')
        equity = metrics.get('equity')
        
        # Revenue Growth would require historical data - placeholder for now
        ratios['revenue_per_employee'] = {
            'value': 'N/A',
            'unit': 'currency',
            'interpretation': 'Requires employee count data',
            'status': 'pending'
        }
        
        # Fixed Asset Ratio
        non_current_assets = metrics.get('non_current_assets')
        if non_current_assets is not None and total_assets and total_assets > 0:
            ratios['fixed_asset_ratio'] = {
                'value': (non_current_assets / total_assets) * 100,
                'unit': '%',
                'interpretation': 'Percentage of assets that are fixed',
                'status': 'success'
            }
        else:
            ratios['fixed_asset_ratio'] = {'status': 'error', 'reason': 'Missing asset data'}
        
        return ratios
    
    def generate_credit_score_inputs(self, metrics: Dict, ratios: Dict) -> Dict:
        """
        Generate inputs for credit scoring based on financial metrics.
        These will be used by the credit scoring engine.
        
        Args:
            metrics: Extracted financial metrics
            ratios: Calculated financial ratios
            
        Returns:
            Dictionary with credit risk indicators
        """
        inputs = {
            'profitability_score': self._score_profitability(ratios.get('profitability_ratios', {})),
            'liquidity_score': self._score_liquidity(ratios.get('liquidity_ratios', {})),
            'solvency_score': self._score_solvency(ratios.get('solvency_ratios', {})),
            'efficiency_score': self._score_efficiency(ratios.get('efficiency_ratios', {})),
            'cash_flow_health': self._assess_cash_flow_health(metrics),
            'leverage_assessment': self._assess_leverage(metrics, ratios),
            'trend_indicators': self._generate_trend_indicators(metrics),
        }
        
        return inputs
    
    def _score_profitability(self, ratios: Dict) -> Dict:
        """Score profitability metrics"""
        score = 0
        max_score = 100
        
        pm = ratios.get('profit_margin', {})
        if pm.get('status') == 'success':
            value = pm.get('value', 0)
            if value >= 10:
                score += 40
            elif value >= 5:
                score += 30
            elif value >= 0:
                score += 15
            else:
                score += 0
        
        roe = ratios.get('return_on_equity', {})
        if roe.get('status') == 'success':
            value = roe.get('value', 0)
            if value >= 15:
                score += 30
            elif value >= 10:
                score += 20
            elif value >= 5:
                score += 10
        
        roa = ratios.get('return_on_assets', {})
        if roa.get('status') == 'success':
            value = roa.get('value', 0)
            if value >= 5:
                score += 30
            elif value >= 2:
                score += 20
            elif value >= 0:
                score += 10
        
        return {
            'score': min(score, max_score),
            'max_score': max_score,
            'assessment': self._get_score_assessment(score / max_score)
        }
    
    def _score_liquidity(self, ratios: Dict) -> Dict:
        """Score liquidity metrics"""
        score = 0
        max_score = 100
        
        cr = ratios.get('current_ratio', {})
        if cr.get('status') == 'success':
            value = cr.get('value', 0)
            if 1.5 <= value <= 3.0:
                score += 40
            elif value >= 1.0:
                score += 20
            elif value >= 0.5:
                score += 10
        
        qr = ratios.get('quick_ratio', {})
        if qr.get('status') == 'success':
            value = qr.get('value', 0)
            if value >= 1.0:
                score += 35
            elif value >= 0.7:
                score += 20
            elif value >= 0.5:
                score += 10
        
        wc = ratios.get('working_capital', {})
        if wc.get('status') == 'success' and wc.get('value', 0) > 0:
            score += 25
        
        return {
            'score': min(score, max_score),
            'max_score': max_score,
            'assessment': self._get_score_assessment(score / max_score)
        }
    
    def _score_solvency(self, ratios: Dict) -> Dict:
        """Score solvency metrics"""
        score = 0
        max_score = 100
        
        de = ratios.get('debt_to_equity', {})
        if de.get('status') == 'success':
            value = de.get('value', 0)
            if value <= 1.0:
                score += 35
            elif value <= 2.0:
                score += 20
            elif value <= 3.0:
                score += 10
        
        ic = ratios.get('interest_coverage', {})
        if ic.get('status') == 'success':
            value = ic.get('value', 0)
            if value >= 2.5:
                score += 35
            elif value >= 1.5:
                score += 20
            elif value >= 1.0:
                score += 10
        
        dsc = ratios.get('debt_service_coverage', {})
        if dsc.get('status') == 'success':
            value = dsc.get('value', 0)
            if value >= 1.25:
                score += 30
            elif value >= 1.0:
                score += 15
        
        return {
            'score': min(score, max_score),
            'max_score': max_score,
            'assessment': self._get_score_assessment(score / max_score)
        }
    
    def _score_efficiency(self, ratios: Dict) -> Dict:
        """Score operational efficiency metrics"""
        score = 0
        max_score = 100
        
        at = ratios.get('asset_turnover', {})
        if at.get('status') == 'success':
            value = at.get('value', 0)
            if value >= 1.5:
                score += 50
            elif value >= 1.0:
                score += 35
            elif value >= 0.5:
                score += 15
        
        it = ratios.get('inventory_turnover', {})
        if it.get('status') == 'success':
            value = it.get('value', 0)
            if value >= 5:
                score += 50
            elif value >= 2:
                score += 30
        
        return {
            'score': min(score, max_score),
            'max_score': max_score,
            'assessment': self._get_score_assessment(score / max_score)
        }
    
    def _assess_cash_flow_health(self, metrics: Dict) -> Dict:
        """Assess cash flow health"""
        ocf = metrics.get('operating_cash_flow')
        net_profit = metrics.get('net_profit')
        
        assessment = {
            'operating_cash_flow': ocf,
            'status': 'unknown',
            'health_score': 0,
            'assessment': 'Insufficient data'
        }
        
        if ocf is not None:
            if ocf > 0:
                assessment['status'] = 'positive'
                assessment['health_score'] = min((ocf / max(net_profit, 1)) * 100, 100)
                assessment['assessment'] = 'Healthy cash generation'
            else:
                assessment['status'] = 'negative'
                assessment['health_score'] = 0
                assessment['assessment'] = 'Negative operating cash flow - concerning'
        
        return assessment
    
    def _assess_leverage(self, metrics: Dict, ratios: Dict) -> Dict:
        """Assess leverage level"""
        de = ratios.get('solvency_ratios', {}).get('debt_to_equity', {})
        
        assessment = {
            'leverage_level': 'unknown',
            'risk_level': 'unknown'
        }
        
        if de.get('status') == 'success':
            value = de.get('value', 0)
            if value <= 0.5:
                assessment['leverage_level'] = 'conservative'
                assessment['risk_level'] = 'low'
            elif value <= 1.5:
                assessment['leverage_level'] = 'moderate'
                assessment['risk_level'] = 'medium'
            elif value <= 3.0:
                assessment['leverage_level'] = 'high'
                assessment['risk_level'] = 'high'
            else:
                assessment['leverage_level'] = 'very_high'
                assessment['risk_level'] = 'very_high'
        
        return assessment
    
    def _generate_trend_indicators(self, metrics: Dict) -> Dict:
        """Generate trend indicators (would use historical data)"""
        return {
            'revenue_trend': 'N/A - requires historical data',
            'profitability_trend': 'N/A - requires historical data',
            'leverage_trend': 'N/A - requires historical data',
            'data_requirements': ['Prior year financial statements', 'Multi-year data for trend analysis']
        }
    
    def _check_current_ratio(self, ratio: float) -> Optional[str]:
        """Check current ratio health"""
        if ratio < 1.0:
            return "⚠️ Current ratio < 1.0: May indicate liquidity issues"
        elif ratio > 5.0:
            return "⚠️ Current ratio > 5.0: May indicate excess liquid assets"
        return None
    
    def _check_debt_to_equity(self, ratio: float) -> Optional[str]:
        """Check debt-to-equity ratio health"""
        if ratio > 3.0:
            return "⚠️ High leverage: D/E > 3.0 indicates strong debt dependence"
        elif ratio < 0.3:
            return "ℹ️ Conservative capital structure: Minimal debt usage"
        return None
    
    def _check_interest_coverage(self, ratio: float) -> Optional[str]:
        """Check interest coverage ratio health"""
        if ratio < 1.5:
            return "⚠️ Low interest coverage: May struggle to pay interest expenses"
        elif ratio < 2.5:
            return "ℹ️ Moderate interest coverage: Some vulnerability to earnings decline"
        return None
    
    def _get_score_assessment(self, normalized_score: float) -> str:
        """Convert score to assessment text"""
        if normalized_score >= 0.8:
            return 'Excellent'
        elif normalized_score >= 0.6:
            return 'Good'
        elif normalized_score >= 0.4:
            return 'Fair'
        elif normalized_score >= 0.2:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def _parse_metric(self, value) -> Optional[float]:
        """Safely parse metric value"""
        try:
            if value is None:
                return None
            return float(value)
        except (ValueError, TypeError):
            return None
