"""
Credit Underwriting Scoring System

Production-grade credit scoring engine for B2B FinTech.
Combines financial metrics, operational factors, and risk indicators
to generate comprehensive credit scores with PD and risk classification.
"""

from typing import Dict, Optional, Tuple
from datetime import datetime
import math


class CreditScoringEngine:
    """
    Comprehensive credit scoring engine combining 8 key metrics:
    - Financial Strength (20%)
    - Bank Relationship Score (15%)
    - Industry Risk Score (15%)
    - Management Quality Score (10%)
    - Collateral Strength (10%)
    - Legal Risk (10%)
    - Fraud Risk (10%)
    - Credit Bureau Score (10%)
    """
    
    # Risk category thresholds
    RISK_THRESHOLDS = {
        'EXCELLENT': (850, 1000),      # Very low default risk
        'VERY_GOOD': (750, 849),       # Low default risk
        'GOOD': (650, 749),            # Moderate-low default risk
        'FAIR': (550, 649),            # Moderate default risk
        'POOR': (450, 549),            # High default risk
        'VERY_POOR': (300, 449),       # Very high default risk
        'UNACCEPTABLE': (0, 299),      # Unacceptable risk
    }
    
    # PD ranges by risk category (%)
    PD_BY_RISK_CATEGORY = {
        'EXCELLENT': (0.05, 0.50),
        'VERY_GOOD': (0.50, 1.00),
        'GOOD': (1.00, 2.50),
        'FAIR': (2.50, 5.00),
        'POOR': (5.00, 10.00),
        'VERY_POOR': (10.00, 25.00),
        'UNACCEPTABLE': (25.00, 100.00),
    }
    
    def __init__(self):
        self.calculated_at = datetime.utcnow()
        self.warnings = []
        self.errors = []
    
    def calculate_credit_score(self, inputs: Dict) -> Dict:
        """
        Main method to calculate comprehensive credit score.
        
        Args:
            inputs: Dictionary containing:
                - financial_metrics: From FinancialMetricsEngine
                - bank_relationship_data: Bank interaction history
                - industry_data: Industry sector info
                - management_quality_data: Management assessment
                - collateral_data: Collateral details
                - legal_compliance_data: Legal status
                - fraud_indicators: Fraud risk signals
                - credit_bureau_data: Credit history
        
        Returns:
            Dictionary with:
                - credit_score: 300-1000
                - probability_of_default: Percentage
                - risk_category: EXCELLENT, VERY_GOOD, etc.
                - component_scores: Individual component scores
                - risk_drivers: Top risk factors
        """
        try:
            # Calculate individual component scores
            financial_strength = self._calculate_financial_strength(
                inputs.get('financial_metrics', {})
            )
            
            bank_relationship = self._calculate_bank_relationship_score(
                inputs.get('bank_relationship_data', {})
            )
            
            industry_risk = self._calculate_industry_risk_score(
                inputs.get('industry_data', {})
            )
            
            management_quality = self._calculate_management_quality_score(
                inputs.get('management_quality_data', {})
            )
            
            collateral_strength = self._calculate_collateral_strength(
                inputs.get('collateral_data', {})
            )
            
            legal_risk = self._calculate_legal_risk_score(
                inputs.get('legal_compliance_data', {})
            )
            
            fraud_risk = self._calculate_fraud_risk_score(
                inputs.get('fraud_indicators', {})
            )
            
            credit_bureau_score = self._calculate_credit_bureau_score(
                inputs.get('credit_bureau_data', {})
            )
            
            # Store component scores
            component_scores = {
                'financial_strength': financial_strength,
                'bank_relationship': bank_relationship,
                'industry_risk': industry_risk,
                'management_quality': management_quality,
                'collateral_strength': collateral_strength,
                'legal_risk': legal_risk,
                'fraud_risk': fraud_risk,
                'credit_bureau_score': credit_bureau_score,
            }
            
            # Calculate weighted final score
            final_score = self._calculate_weighted_score(component_scores)
            
            # Determine risk category
            risk_category = self._get_risk_category(final_score)
            
            # Calculate probability of default
            probability_of_default = self._calculate_probability_of_default(
                final_score,
                risk_category
            )
            
            # Identify key risk drivers
            risk_drivers = self._identify_risk_drivers(component_scores, final_score)
            
            # Generate credit recommendation
            recommendation = self._generate_recommendation(
                final_score,
                risk_category,
                probability_of_default,
                risk_drivers
            )
            
            return {
                'credit_score': final_score,
                'probability_of_default': probability_of_default,
                'risk_category': risk_category,
                'component_scores': component_scores,
                'risk_drivers': risk_drivers,
                'recommendation': recommendation,
                'calculation_status': 'success',
                'warnings': self.warnings,
                'errors': self.errors,
                'calculated_at': self.calculated_at,
            }
        
        except Exception as e:
            self.errors.append(f"Error calculating credit score: {str(e)}")
            return {
                'credit_score': None,
                'probability_of_default': None,
                'risk_category': 'UNACCEPTABLE',
                'component_scores': {},
                'calculation_status': 'error',
                'warnings': self.warnings,
                'errors': self.errors,
                'error_message': str(e),
            }
    
    def _calculate_financial_strength(self, financial_metrics: Dict) -> int:
        """
        Calculate financial strength score (0-100).
        Based on profitability, liquidity, solvency from metrics engine.
        
        Scoring:
        - Profitability Score: 30% (profit, margins, EBITDA)
        - Liquidity Score: 30% (working capital, current ratio)
        - Solvency Score: 40% (debt ratios, coverage ratios)
        """
        try:
            # Extract scores from financial metrics
            profitability = financial_metrics.get('profitability_score', 0)
            liquidity = financial_metrics.get('liquidity_score', 0)
            solvency = financial_metrics.get('solvency_score', 0)
            
            if not any([profitability, liquidity, solvency]):
                self.warnings.append("No financial metrics provided")
                return 50  # Default to neutral
            
            # Weighted calculation
            financial_strength = (
                profitability * 0.30 +
                liquidity * 0.30 +
                solvency * 0.40
            )
            
            # Cap at 100
            financial_strength = min(financial_strength, 100)
            
            # Convert to 0-100 scale if needed
            return int(financial_strength)
        
        except Exception as e:
            self.warnings.append(f"Error in financial strength: {str(e)}")
            return 50
    
    def _calculate_bank_relationship_score(self, bank_data: Dict) -> int:
        """
        Calculate bank relationship score (0-100).
        
        Factors:
        - Years of relationship (0-30 points)
        - Transaction volume (0-25 points)
        - Credit facility utilization (0-20 points)
        - Overdraft history (0-15 points)
        - Timeliness of payments (0-10 points)
        """
        try:
            score = 0
            
            # Years of relationship
            years = bank_data.get('relationship_years', 0)
            if years >= 5:
                score += 30
            elif years >= 3:
                score += 20
            elif years >= 1:
                score += 10
            else:
                score += 5
                self.warnings.append("Less than 1 year bank relationship")
            
            # Transaction volume (monthly average)
            monthly_volume = bank_data.get('avg_monthly_transaction_volume', 0)
            if monthly_volume > 10000000:  # >₹1 crore
                score += 25
            elif monthly_volume > 5000000:  # >₹50 lakh
                score += 20
            elif monthly_volume > 1000000:  # >₹10 lakh
                score += 15
            else:
                score += 5
            
            # Facility utilization ratio
            utilization = bank_data.get('credit_facility_utilization', 0)  # 0-1
            if 0.4 <= utilization <= 0.8:
                score += 20
            elif utilization <= 0.4:
                score += 10
            elif utilization <= 1.0:
                score += 15
            else:
                score += 0
            
            # Overdraft incidents
            overdraft_incidents = bank_data.get('overdraft_incidents_6m', 0)
            if overdraft_incidents == 0:
                score += 15
            elif overdraft_incidents <= 2:
                score += 10
            elif overdraft_incidents <= 5:
                score += 5
            else:
                score += 0
            
            # Payment timeliness
            payment_delay_days = bank_data.get('avg_payment_delay_days', 0)
            if payment_delay_days <= 5:
                score += 10
            elif payment_delay_days <= 15:
                score += 5
            else:
                score += 0
            
            return min(score, 100)
        
        except Exception as e:
            self.warnings.append(f"Error in bank relationship: {str(e)}")
            return 50
    
    def _calculate_industry_risk_score(self, industry_data: Dict) -> int:
        """
        Calculate industry risk score (0-100).
        
        Factors:
        - Industry sector risk (0-35 points)
        - Market position/competition (0-25 points)
        - Growth trajectory (0-20 points)
        - Economic sensitivity (0-20 points)
        """
        try:
            score = 0
            
            # Industry sector risk
            sector = industry_data.get('sector', 'IT')
            sector_risk_scores = {
                'IT': 90,              # IT Services - low risk
                'PHARMA': 85,          # Pharmaceuticals - low risk
                'MANUFACTURING': 70,   # Manufacturing - moderate risk
                'RETAIL': 60,          # Retail - higher risk
                'CONSTRUCTION': 50,    # Construction - high risk
                'TEXTILE': 50,         # Textiles - high risk
                'REAL_ESTATE': 40,     # Real Estate - high risk
                'HOSPITALITY': 45,     # Hospitality - high risk
                'AVIATION': 40,        # Aviation - high risk
            }
            
            sector_score = sector_risk_scores.get(sector, 60)
            score += (sector_score / 100) * 35
            
            # Market position (1 = strong, 0.5 = moderate, 0 = weak)
            market_position = industry_data.get('market_position', 0.5)
            score += market_position * 25
            
            # Growth trajectory (1 = growing, 0.5 = stable, 0 = declining)
            growth = industry_data.get('growth_trajectory', 0.5)
            score += growth * 20
            
            # Economic sensitivity (1 = low, 0.5 = moderate, 0 = high)
            econ_sensitivity = industry_data.get('economic_sensitivity', 0.5)
            score += econ_sensitivity * 20
            
            return min(int(score), 100)
        
        except Exception as e:
            self.warnings.append(f"Error in industry risk: {str(e)}")
            return 60
    
    def _calculate_management_quality_score(self, mgmt_data: Dict) -> int:
        """
        Calculate management quality score (0-100).
        
        Factors:
        - Management experience (0-30 points)
        - Educational qualification (0-20 points)
        - Track record (0-25 points)
        - Industry expertise (0-15 points)
        - Regulatory compliance record (0-10 points)
        """
        try:
            score = 0
            
            # Management experience
            avg_exp = mgmt_data.get('avg_experience_years', 0)
            if avg_exp >= 15:
                score += 30
            elif avg_exp >= 10:
                score += 25
            elif avg_exp >= 5:
                score += 15
            else:
                score += 5
                self.warnings.append("Limited management experience")
            
            # Educational qualification (% with postgraduate)
            postgrad_pct = mgmt_data.get('postgraduate_percentage', 0)
            score += min(postgrad_pct / 5, 20)  # Max 20 points
            
            # Track record (previous ventures success rate)
            success_rate = mgmt_data.get('previous_ventures_success_rate', 0)  # 0-1
            score += success_rate * 25
            
            # Industry expertise (years in same industry)
            industry_exp = mgmt_data.get('industry_experience_years', 0)
            if industry_exp >= 10:
                score += 15
            elif industry_exp >= 5:
                score += 10
            else:
                score += 5
            
            # Compliance record (0-1)
            compliance_score = mgmt_data.get('compliance_record_score', 0.5)
            score += compliance_score * 10
            
            return min(int(score), 100)
        
        except Exception as e:
            self.warnings.append(f"Error in management quality: {str(e)}")
            return 50
    
    def _calculate_collateral_strength(self, collateral_data: Dict) -> int:
        """
        Calculate collateral strength score (0-100).
        
        Factors:
        - Collateral to loan ratio (0-40 points)
        - Quality of collateral (0-35 points)
        - Liquidity of collateral (0-25 points)
        """
        try:
            score = 0
            
            # Collateral to loan ratio
            loan_amount = collateral_data.get('loan_amount', 1)
            collateral_value = collateral_data.get('collateral_value', 0)
            
            if collateral_value == 0:
                score += 0
                self.warnings.append("Unsecured loan - no collateral")
            else:
                cl_ratio = collateral_value / loan_amount
                if cl_ratio >= 2.0:
                    score += 40
                elif cl_ratio >= 1.5:
                    score += 35
                elif cl_ratio >= 1.0:
                    score += 25
                elif cl_ratio >= 0.75:
                    score += 15
                else:
                    score += 5
            
            # Quality of collateral
            collateral_type = collateral_data.get('collateral_type', 'UNSECURED')
            quality_scores = {
                'PROPERTY': 90,        # Real estate - highest quality
                'GOLD': 85,           # Gold - very high quality
                'SECURITIES': 80,     # Securities - high quality
                'EQUIPMENT': 60,      # Equipment - moderate quality
                'INVENTORY': 50,      # Inventory - lower quality
                'RECEIVABLES': 40,    # Receivables - low quality
                'UNSECURED': 0,       # Unsecured
            }
            
            quality_score = quality_scores.get(collateral_type, 0)
            score += (quality_score / 100) * 35
            
            # Liquidity of collateral (days to liquidate)
            liquidation_days = collateral_data.get('liquidation_days', 365)
            if liquidation_days <= 30:
                score += 25
            elif liquidation_days <= 90:
                score += 20
            elif liquidation_days <= 180:
                score += 15
            else:
                score += 5
            
            return min(int(score), 100)
        
        except Exception as e:
            self.warnings.append(f"Error in collateral strength: {str(e)}")
            return 40
    
    def _calculate_legal_risk_score(self, legal_data: Dict) -> int:
        """
        Calculate legal risk score (0-100).
        
        Factors:
        - Legal entity status (0-25 points)
        - Regulatory compliance (0-25 points)
        - Litigation history (0-20 points)
        - Regulatory violations (0-15 points)
        - Bankruptcy history (0-15 points)
        """
        try:
            score = 0
            
            # Legal entity status
            entity_status = legal_data.get('entity_status', 'ACTIVE')
            status_scores = {
                'ACTIVE': 25,
                'ACTIVE_WITH_CAUTION': 15,
                'SUSPENDED': 0,
                'DEACTIVATED': 0,
            }
            score += status_scores.get(entity_status, 10)
            
            # Regulatory compliance
            compliance_score = legal_data.get('regulatory_compliance_score', 0.7)  # 0-1
            score += compliance_score * 25
            
            # Litigation history (number of cases in last 3 years)
            litigation_cases = legal_data.get('active_litigation_cases', 0)
            if litigation_cases == 0:
                score += 20
            elif litigation_cases <= 2:
                score += 10
            else:
                score += 0
            
            # Regulatory violations (number in last 5 years)
            violations = legal_data.get('regulatory_violations_count', 0)
            if violations == 0:
                score += 15
            elif violations == 1:
                score += 10
            elif violations == 2:
                score += 5
            else:
                score += 0
            
            # Bankruptcy history
            bankruptcy_days_ago = legal_data.get('bankruptcy_days_ago', 10000)
            if bankruptcy_days_ago > 1825:  # >5 years
                score += 15
            elif bankruptcy_days_ago > 365:  # >1 year
                score += 5
            else:
                score += 0
                self.errors.append("Bankruptcy within last 1 year")
            
            return min(int(score), 100)
        
        except Exception as e:
            self.warnings.append(f"Error in legal risk: {str(e)}")
            return 50
    
    def _calculate_fraud_risk_score(self, fraud_data: Dict) -> int:
        """
        Calculate fraud risk score (0-100).
        Higher score = lower risk
        
        Factors:
        - Fraud investigation history (0-25 points)
        - Document authenticity (0-25 points)
        - Financial statement consistency (0-25 points)
        - Identity verification (0-15 points)
        - Red flags (0-10 points)
        """
        try:
            score = 100  # Start high
            
            # Fraud history
            fraud_investigations = fraud_data.get('fraud_investigations_count', 0)
            if fraud_investigations > 0:
                score -= fraud_investigations * 25
                self.errors.append(f"Fraud investigations found: {fraud_investigations}")
            
            # Document authenticity check (0-1)
            doc_authenticity = fraud_data.get('document_authenticity_score', 1.0)
            score -= (1.0 - doc_authenticity) * 25
            
            # Financial statement consistency (0-1)
            financial_consistency = fraud_data.get('financial_consistency_score', 1.0)
            score -= (1.0 - financial_consistency) * 25
            
            # Identity verification (0-1)
            identity_verified = fraud_data.get('identity_verification_score', 1.0)
            score -= (1.0 - identity_verified) * 15
            
            # Red flags count
            red_flags = fraud_data.get('red_flags_count', 0)
            if red_flags > 0:
                score -= min(red_flags * 2, 10)
            
            return max(int(score), 0)
        
        except Exception as e:
            self.warnings.append(f"Error in fraud risk: {str(e)}")
            return 50
    
    def _calculate_credit_bureau_score(self, bureau_data: Dict) -> int:
        """
        Calculate credit bureau score (0-100).
        Based on credit history and bureau reports.
        
        Factors:
        - Credit score (if available) (0-40 points)
        - Payment default history (0-30 points)
        - Credit utilization (0-15 points)
        - Credit age (0-15 points)
        """
        try:
            score = 0
            
            # Credit bureau score (if available, typically 300-900)
            bureau_score = bureau_data.get('credit_bureau_score', None)
            if bureau_score:
                # Normalize 300-900 to 0-40
                normalized = ((bureau_score - 300) / 600) * 40
                score += min(normalized, 40)
            else:
                # Use alternative metrics
                self.warnings.append("No credit bureau score available")
            
            # Payment default history (number of defaults in last 24 months)
            defaults = bureau_data.get('payment_defaults_24m', 0)
            if defaults == 0:
                score += 30
            elif defaults == 1:
                score += 15
            elif defaults == 2:
                score += 5
            else:
                score += 0
            
            # Credit utilization ratio (0-1)
            utilization_ratio = bureau_data.get('credit_utilization_ratio', 0.5)
            if utilization_ratio <= 0.30:
                score += 15
            elif utilization_ratio <= 0.70:
                score += 10
            else:
                score += 0
            
            # Credit age (oldest active account in months)
            credit_age_months = bureau_data.get('credit_age_months', 12)
            if credit_age_months >= 60:
                score += 15
            elif credit_age_months >= 36:
                score += 10
            elif credit_age_months >= 12:
                score += 5
            else:
                score += 0
            
            return min(int(score), 100)
        
        except Exception as e:
            self.warnings.append(f"Error in credit bureau: {str(e)}")
            return 50
    
    def _calculate_weighted_score(self, component_scores: Dict) -> int:
        """
        Calculate final credit score using weighted average.
        
        Weights:
        - Financial Strength: 20%
        - Bank Relationship: 15%
        - Industry Risk: 15%
        - Management Quality: 10%
        - Collateral Strength: 10%
        - Legal Risk: 10%
        - Fraud Risk: 10%
        - Credit Bureau: 10%
        
        Scale: 300-1000 (mapping from 0-100 component scores)
        """
        weighted_score = (
            component_scores.get('financial_strength', 50) * 0.20 +
            component_scores.get('bank_relationship', 50) * 0.15 +
            component_scores.get('industry_risk', 50) * 0.15 +
            component_scores.get('management_quality', 50) * 0.10 +
            component_scores.get('collateral_strength', 50) * 0.10 +
            component_scores.get('legal_risk', 50) * 0.10 +
            component_scores.get('fraud_risk', 50) * 0.10 +
            component_scores.get('credit_bureau_score', 50) * 0.10
        )
        
        # Scale from 0-100 to 300-1000
        final_score = 300 + (weighted_score * 7)  # 300 + (0-100)*7 = 300-1000
        
        return int(final_score)
    
    def _get_risk_category(self, credit_score: int) -> str:
        """Determine risk category from credit score."""
        for category, (lower, upper) in self.RISK_THRESHOLDS.items():
            if lower <= credit_score <= upper:
                return category
        return 'UNACCEPTABLE'
    
    def _calculate_probability_of_default(self, credit_score: int, risk_category: str) -> float:
        """
        Calculate probability of default as percentage.
        Uses logistic regression formula based on credit score.
        
        Formula: PD = 1 / (1 + e^((credit_score - 650) / 100))
        """
        try:
            # Logistic regression model
            x = (credit_score - 650) / 100
            pd = 1 / (1 + math.exp(x))
            pd_percentage = pd * 100
            
            # Ensure within risk category bounds
            if risk_category in self.PD_BY_RISK_CATEGORY:
                lower, upper = self.PD_BY_RISK_CATEGORY[risk_category]
                pd_percentage = max(lower, min(upper, pd_percentage))
            
            return round(pd_percentage, 2)
        
        except Exception as e:
            self.warnings.append(f"Error calculating PD: {str(e)}")
            return 50.0
    
    def _identify_risk_drivers(self, component_scores: Dict, final_score: int) -> Dict:
        """
        Identify the top risk drivers affecting the score.
        """
        risk_drivers = {
            'primary_risk_drivers': [],
            'strength_areas': [],
            'improvement_areas': [],
        }
        
        # Identify weak areas (scores < 50)
        weak_components = [
            (name, score) for name, score in component_scores.items()
            if isinstance(score, (int, float)) and score < 50
        ]
        
        # Sort by lowest score
        weak_components.sort(key=lambda x: x[1])
        
        risk_drivers['primary_risk_drivers'] = [
            {
                'factor': name.replace('_', ' ').title(),
                'score': score,
                'impact': 'High' if score < 30 else 'Medium'
            }
            for name, score in weak_components[:3]
        ]
        
        # Identify strong areas (scores >= 75)
        strong_components = [
            (name, score) for name, score in component_scores.items()
            if isinstance(score, (int, float)) and score >= 75
        ]
        
        strong_components.sort(key=lambda x: x[1], reverse=True)
        
        risk_drivers['strength_areas'] = [
            {
                'factor': name.replace('_', ' ').title(),
                'score': score
            }
            for name, score in strong_components[:3]
        ]
        
        # Improvement areas (50-75 range)
        improvement_components = [
            (name, score) for name, score in component_scores.items()
            if isinstance(score, (int, float)) and 50 <= score < 75
        ]
        
        improvement_components.sort(key=lambda x: x[1])
        
        risk_drivers['improvement_areas'] = [
            {
                'factor': name.replace('_', ' ').title(),
                'score': score,
                'potential_improvement': 75 - score
            }
            for name, score in improvement_components[:3]
        ]
        
        return risk_drivers
    
    def _generate_recommendation(
        self,
        credit_score: int,
        risk_category: str,
        probability_of_default: float,
        risk_drivers: Dict
    ) -> Dict:
        """
        Generate credit decision recommendation.
        """
        recommendations = {
            'EXCELLENT': {
                'decision': 'APPROVED',
                'rationale': 'Very low default risk. Strong financials and payment history.',
                'conditions': [],
                'recommended_rate_adjustment': -100,  # Basis points reduction
            },
            'VERY_GOOD': {
                'decision': 'APPROVED',
                'rationale': 'Low default risk. Good financial position and credit history.',
                'conditions': ['Monitor quarterly financials'],
                'recommended_rate_adjustment': -50,
            },
            'GOOD': {
                'decision': 'APPROVED',
                'rationale': 'Moderate-low default risk. Acceptable credit profile.',
                'conditions': [
                    'Quarterly financial monitoring',
                    'Annual review',
                    'Security review',
                ],
                'recommended_rate_adjustment': 0,
            },
            'FAIR': {
                'decision': 'APPROVED_WITH_CONDITIONS',
                'rationale': 'Moderate default risk. Enhanced monitoring required.',
                'conditions': [
                    'Quarterly financial statements mandatory',
                    'Personal guarantee required',
                    'Enhanced security',
                    'Regular review meetings (6-monthly)',
                ],
                'recommended_rate_adjustment': 100,
            },
            'POOR': {
                'decision': 'APPROVED_WITH_STRONG_CONDITIONS',
                'rationale': 'High default risk. Significant risk mitigation required.',
                'conditions': [
                    'Monthly financial statements',
                    'Enhanced collateral (150%+)',
                    'Personal/corporate guarantee',
                    'Quarterly review meetings',
                    'Director personal guarantee',
                    'Restricted fund usage',
                ],
                'recommended_rate_adjustment': 250,
            },
            'VERY_POOR': {
                'decision': 'DECLINED_OR_SUBSTANTIAL_CONDITIONS',
                'rationale': 'Very high default risk. Unacceptable risk profile.',
                'conditions': [
                    'Decline recommended unless significant improvements',
                    'If approved: Charge restrictive rate',
                    'Require 200%+ collateral',
                    'Monthly monitoring',
                    'Director/promoter personal guarantee',
                ],
                'recommended_rate_adjustment': 500,
            },
            'UNACCEPTABLE': {
                'decision': 'DECLINED',
                'rationale': 'Unacceptable credit risk.',
                'conditions': ['Recommend decline'],
                'recommended_rate_adjustment': 1000,
            },
        }
        
        recommendation = recommendations.get(risk_category, recommendations['UNACCEPTABLE']).copy()
        
        # Add specific advice based on risk drivers
        if risk_drivers.get('primary_risk_drivers'):
            recommendation['specific_advice'] = f"Address: {', '.join([d['factor'] for d in risk_drivers['primary_risk_drivers'][:2]])}"
        
        return recommendation
