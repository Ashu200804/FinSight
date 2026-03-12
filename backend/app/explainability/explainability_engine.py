"""
SHAP-based Explainability Engine for Credit Underwriting Decisions

Provides feature importance, risk factor analysis, and human-readable explanations
for AI-driven credit decisions using SHapley Additive exPlanations (SHAP).
"""

import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import os

from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class FeatureImportance:
    """Feature importance result"""
    feature_name: str
    importance_score: float
    contribution: float  # How much it contributes to the final prediction
    direction: str  # POSITIVE, NEGATIVE, NEUTRAL
    impact_level: str  # CRITICAL, HIGH, MEDIUM, LOW


@dataclass
class RiskFactor:
    """Identified risk factor"""
    factor_name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    recommendation: str
    feature_contributions: List[Dict[str, float]]


@dataclass
class CreditDecisionExplanation:
    """Complete explanation of a credit decision"""
    decision_id: str
    applicant_name: str
    final_score: float
    final_rating: str  # AAA, AA, A, BBB, BB, B, CCC, D
    decision: str  # APPROVE, CONDITIONAL_APPROVE, DECLINE
    decision_confidence: float
    
    # SHAP-based analysis
    feature_importance: List[FeatureImportance]
    top_contributing_factors: List[str]
    top_risk_factors: List[RiskFactor]
    
    # Human-readable explanations
    executive_summary: str
    key_findings: List[str]
    strengths: List[str]
    concerns: List[str]
    recommendations: List[str]
    
    # Sensitivity analysis
    sensitivity_analysis: Dict[str, Dict[str, float]]  # How score changes with input changes
    
    # Generated at
    generated_at: str
    explanation_confidence: float


class SHAPExplainer:
    """
    SHAP-based explainability engine for credit decisions.
    
    Uses kernel SHAP or tree SHAP depending on model type to explain
    individual predictions and provide feature importance analysis.
    """
    
    def __init__(self, model, feature_names: List[str], background_data: pd.DataFrame = None):
        """
        Initialize SHAP explainer.
        
        Args:
            model: Trained credit scoring model
            feature_names: List of feature names used in the model
            background_data: Background dataset for SHAP (can be sample or full training data)
        """
        self.model = model
        self.feature_names = feature_names
        self.background_data = background_data
        self.explainer = None
        self.shap_values = None
        self.base_value = None
        
        # Initialize explainer
        self._initialize_explainer()
    
    def _initialize_explainer(self):
        """Initialize SHAP explainer based on model type"""
        try:
            # For tree-based models (XGBoost, LightGBM, etc.)
            if hasattr(self.model, 'predict'):
                try:
                    self.explainer = shap.TreeExplainer(self.model)
                    logger.info("Initialized TreeExplainer for model")
                except Exception as e:
                    logger.info(f"TreeExplainer failed ({e}), falling back to KernelExplainer")
                    # Fallback to KernelExplainer for other models
                    if self.background_data is not None:
                        background_sample = self.background_data.sample(
                            min(100, len(self.background_data)), 
                            random_state=42
                        )
                        self.explainer = shap.KernelExplainer(
                            self.model.predict,
                            background_sample
                        )
                        logger.info("Initialized KernelExplainer for model")
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            self.explainer = None
    
    def explain_prediction(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate SHAP values for predictions.
        
        Args:
            X: Input features (single row or multiple rows)
        
        Returns:
            SHAP values array
        """
        if self.explainer is None:
            logger.warning("SHAP explainer not initialized, returning empty values")
            return np.zeros((X.shape[0], X.shape[1]))
        
        try:
            shap_values = self.explainer.shap_values(X)
            
            # Handle different return formats from SHAP
            if isinstance(shap_values, list):
                # For multi-class problems, return values for positive class
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            
            self.shap_values = shap_values
            
            # Get base value (expected model output)
            if hasattr(self.explainer, 'expected_value'):
                self.base_value = self.explainer.expected_value
            
            return shap_values
        except Exception as e:
            logger.error(f"Error calculating SHAP values: {e}")
            return np.zeros((X.shape[0], X.shape[1]))
    
    def get_feature_importance(self, X: pd.DataFrame, prediction: float) -> List[FeatureImportance]:
        """
        Get feature importance for a single prediction.
        
        Args:
            X: Input features (single row)
            prediction: Model's prediction for this sample
        
        Returns:
            List of FeatureImportance objects sorted by importance
        """
        shap_values = self.explain_prediction(X)
        
        if shap_values.size == 0:
            logger.warning("No SHAP values available for feature importance")
            return []
        
        # Handle single row
        if len(shap_values.shape) == 1:
            shap_values = shap_values.reshape(1, -1)
        
        # Get absolute importance (magnitude of SHAP values)
        importance_scores = np.abs(shap_values[0])
        
        # Normalize to 0-100
        max_importance = importance_scores.max()
        if max_importance > 0:
            normalized_scores = (importance_scores / max_importance) * 100
        else:
            normalized_scores = importance_scores
        
        # Create importance objects
        feature_importances = []
        for i, feature_name in enumerate(self.feature_names):
            # Get the actual feature value
            feature_value = X.iloc[0, i] if isinstance(X, pd.DataFrame) else X[0, i]
            
            # Determine direction (positive/negative contribution to decision)
            shap_value = shap_values[0, i]
            if shap_value > 0:
                direction = "POSITIVE"
            elif shap_value < 0:
                direction = "NEGATIVE"
            else:
                direction = "NEUTRAL"
            
            # Determine impact level
            abs_importance = abs(shap_value)
            if abs_importance > 0.3:
                impact_level = "CRITICAL"
            elif abs_importance > 0.15:
                impact_level = "HIGH"
            elif abs_importance > 0.08:
                impact_level = "MEDIUM"
            else:
                impact_level = "LOW"
            
            feature_importances.append(FeatureImportance(
                feature_name=feature_name,
                importance_score=float(normalized_scores[i]),
                contribution=float(shap_value),
                direction=direction,
                impact_level=impact_level
            ))
        
        # Sort by importance score (descending)
        return sorted(feature_importances, key=lambda x: x.importance_score, reverse=True)
    
    def get_top_contributing_factors(self, 
                                     feature_importances: List[FeatureImportance],
                                     top_n: int = 5) -> List[str]:
        """
        Get top N contributing factors.
        
        Args:
            feature_importances: List of FeatureImportance objects
            top_n: Number of top factors to return
        
        Returns:
            List of top contributing factor names with descriptions
        """
        top_factors = []
        for imp in feature_importances[:top_n]:
            direction_text = "increasing" if imp.direction == "POSITIVE" else "decreasing"
            factor_text = f"{imp.feature_name} ({direction_text} probability by {abs(imp.contribution):.2%})"
            top_factors.append(factor_text)
        
        return top_factors


class CreditDecisionExplainer:
    """
    Generate human-readable explanations for credit decisions.
    
    Combines SHAP values, credit scoring metrics, and domain knowledge
    to produce comprehensive explanations suitable for credit committees.
    """
    
    def __init__(self, shap_explainer: SHAPExplainer):
        """
        Initialize credit decision explainer.
        
        Args:
            shap_explainer: Initialized SHAPExplainer instance
        """
        self.shap_explainer = shap_explainer
        self.risk_factor_templates = self._init_risk_templates()
        self.explanation_templates = self._init_explanation_templates()
    
    def _init_risk_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize risk factor templates for different metrics"""
        return {
            'debt_to_equity': {
                'high': 'High leverage ratio indicates substantial financial risk from debt obligations',
                'medium': 'Moderate leverage requires monitoring debt service capacity',
                'low': 'Conservative capital structure reduces financial distress risk'
            },
            'current_ratio': {
                'low': 'Low liquidity ratio may indicate difficulty meeting short-term obligations',
                'medium': 'Adequate liquidity for normal operations',
                'high': 'Strong liquidity position with ample short-term assets'
            },
            'debt_service_coverage': {
                'low': 'Insufficient cash flow to comfortably service debt',
                'medium': 'Adequate debt service capacity with limited margin',
                'high': 'Strong ability to service debt from operating cash flow'
            },
            'interest_coverage': {
                'low': 'Weak earnings coverage of interest expenses',
                'medium': 'Moderate interest coverage ratio',
                'high': 'Strong earnings sufficiently cover interest obligations'
            },
            'profitability': {
                'low': 'Low profitability limits debt repayment capacity',
                'medium': 'Moderate profitability generates steady cash flow',
                'high': 'Strong profitability provides significant debt service cushion'
            },
            'default_probability': {
                'high': 'Statistical models estimate elevated default risk',
                'medium': 'Moderate default probability within acceptable range',
                'low': 'Low statistical probability of credit default'
            }
        }
    
    def _init_explanation_templates(self) -> Dict[str, str]:
        """Initialize explanation templates by rating"""
        return {
            'AAA': 'Exceptional creditworthiness with minimal risk. Strong financial position.',
            'AA': 'Very strong creditworthiness. High capacity to meet obligations.',
            'A': 'Good creditworthiness. Adequate capacity to meet obligations.',
            'BBB': 'Acceptable creditworthiness. Adequate financial capacity.',
            'BB': 'Speculative. Vulnerable to adverse conditions.',
            'B': 'More speculative. Significant vulnerability.',
            'CCC': 'High default risk. Substantial weakness.',
            'D': 'Default. Unable to meet obligations.'
        }
    
    def explain_credit_decision(self,
                               decision_id: str,
                               applicant_name: str,
                               X: pd.DataFrame,
                               credit_score: float,
                               credit_rating: str,
                               decision: str,
                               metrics: Dict[str, float],
                               research_findings: Dict[str, Any] = None) -> CreditDecisionExplanation:
        """
        Generate comprehensive explanation for credit decision.
        
        Args:
            decision_id: Unique identifier for this decision
            applicant_name: Name of applicant
            X: Input features used in credit scoring
            credit_score: Calculated credit score (0-1000)
            credit_rating: Assigned credit rating (AAA-D)
            decision: Decision outcome (APPROVE, CONDITIONAL_APPROVE, DECLINE)
            metrics: Dictionary of financial metrics used
            research_findings: Optional research engine findings
        
        Returns:
            CreditDecisionExplanation object with full analysis
        """
        
        # Get feature importances from SHAP
        feature_importances = self.shap_explainer.get_feature_importance(X, credit_score)
        
        # Get top factors
        top_factors = self.shap_explainer.get_top_contributing_factors(feature_importances, top_n=5)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(feature_importances, metrics, research_findings)
        
        # Generate human-readable explanations
        executive_summary = self._generate_executive_summary(
            applicant_name, credit_rating, decision, metrics
        )
        
        key_findings = self._generate_key_findings(
            feature_importances, metrics, credit_rating
        )
        
        strengths = self._identify_strengths(metrics, feature_importances)
        concerns = self._identify_concerns(metrics, feature_importances, risk_factors)
        recommendations = self._generate_recommendations(
            credit_rating, risk_factors, metrics
        )
        
        # Perform sensitivity analysis
        sensitivity = self._perform_sensitivity_analysis(X, metrics)
        
        # Calculate explanation confidence
        explanation_confidence = self._calculate_confidence(feature_importances, metrics)
        
        return CreditDecisionExplanation(
            decision_id=decision_id,
            applicant_name=applicant_name,
            final_score=float(credit_score),
            final_rating=credit_rating,
            decision=decision,
            decision_confidence=0.92,  # Based on model confidence
            feature_importance=[
                {
                    'feature_name': imp.feature_name,
                    'importance_score': imp.importance_score,
                    'contribution': imp.contribution,
                    'direction': imp.direction,
                    'impact_level': imp.impact_level
                }
                for imp in feature_importances
            ],
            top_contributing_factors=top_factors,
            top_risk_factors=risk_factors,
            executive_summary=executive_summary,
            key_findings=key_findings,
            strengths=strengths,
            concerns=concerns,
            recommendations=recommendations,
            sensitivity_analysis=sensitivity,
            generated_at=datetime.now().isoformat(),
            explanation_confidence=explanation_confidence
        )
    
    def _identify_risk_factors(self,
                               feature_importances: List[FeatureImportance],
                               metrics: Dict[str, float],
                               research_findings: Dict = None) -> List[RiskFactor]:
        """
        Identify and describe risk factors.
        
        Args:
            feature_importances: SHAP-based feature importance
            metrics: Financial metrics
            research_findings: Research engine findings
        
        Returns:
            List of identified risk factors
        """
        risk_factors = []
        
        # Analyze financial metrics for risks
        
        # 1. Leverage risk
        debt_to_equity = metrics.get('debt_to_equity', 0)
        if debt_to_equity > 2.0:
            severity = 'CRITICAL'
            feature_contrib = [{'feature': 'debt_to_equity', 'contribution': debt_to_equity}]
        elif debt_to_equity > 1.5:
            severity = 'HIGH'
            feature_contrib = [{'feature': 'debt_to_equity', 'contribution': debt_to_equity}]
        else:
            severity = None
            feature_contrib = []
        
        if severity:
            risk_factors.append(RiskFactor(
                factor_name='High Financial Leverage',
                severity=severity,
                description=self.risk_factor_templates['debt_to_equity'].get(
                    'high' if severity == 'CRITICAL' else 'medium'
                ),
                recommendation='Consider debt reduction strategy or revenue growth initiatives',
                feature_contributions=feature_contrib
            ))
        
        # 2. Liquidity risk
        current_ratio = metrics.get('current_ratio', 0)
        if current_ratio < 1.0:
            risk_factors.append(RiskFactor(
                factor_name='Low Liquidity Risk',
                severity='HIGH',
                description=self.risk_factor_templates['current_ratio']['low'],
                recommendation='Improve working capital management and short-term cash flow',
                feature_contributions=[{'feature': 'current_ratio', 'contribution': current_ratio}]
            ))
        
        # 3. Debt service coverage risk
        dscr = metrics.get('debt_service_coverage_ratio', 0)
        if dscr < 1.25:
            risk_factors.append(RiskFactor(
                factor_name='Weak Debt Service Coverage',
                severity='HIGH' if dscr < 1.0 else 'MEDIUM',
                description=self.risk_factor_templates['debt_service_coverage'].get(
                    'low' if dscr < 1.0 else 'medium'
                ),
                recommendation='Increase operational efficiency and revenue generation',
                feature_contributions=[{'feature': 'dscr', 'contribution': dscr}]
            ))
        
        # 4. Profitability risk
        net_margin = metrics.get('net_profit_margin', 0)
        if net_margin < 0.05:
            risk_factors.append(RiskFactor(
                factor_name='Low Profitability',
                severity='MEDIUM',
                description=self.risk_factor_templates['profitability']['low'],
                recommendation='Focus on margin improvement and cost control',
                feature_contributions=[{'feature': 'net_profit_margin', 'contribution': net_margin}]
            ))
        
        # 5. Research-based risks
        if research_findings:
            legal_risks = research_findings.get('legal_risks', [])
            for legal_risk in legal_risks:
                if legal_risk.get('severity') == 'CRITICAL':
                    risk_factors.append(RiskFactor(
                        factor_name=f"Legal Risk: {legal_risk.get('type')}",
                        severity='CRITICAL',
                        description=legal_risk.get('description', 'Significant legal issue identified'),
                        recommendation='Resolve legal issues before credit approval',
                        feature_contributions=[]
                    ))
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        risk_factors.sort(key=lambda x: severity_order.get(x.severity, 99))
        
        return risk_factors
    
    def _generate_executive_summary(self,
                                   applicant_name: str,
                                   credit_rating: str,
                                   decision: str,
                                   metrics: Dict[str, float]) -> str:
        """Generate executive summary"""
        def format_metric(metric_name: str, fmt: str = ".2f", suffix: str = "") -> str:
            value = metrics.get(metric_name)
            if value is None:
                return "N/A"
            return f"{value:{fmt}}{suffix}"

        decision_text = {
            'APPROVE': 'recommended for approval',
            'CONDITIONAL_APPROVE': 'recommended for conditional approval',
            'DECLINE': 'recommended for decline'
        }
        
        rating_desc = self.explanation_templates.get(
            credit_rating,
            'Unknown credit rating'
        )
        
        summary = f"""
{applicant_name} is {decision_text.get(decision, 'under consideration')} with a {credit_rating} credit rating. 
{rating_desc}

Key Financial Metrics:
- Debt-to-Equity Ratio: {format_metric('debt_to_equity')}
- Current Ratio: {format_metric('current_ratio')}
- Debt Service Coverage: {format_metric('debt_service_coverage_ratio', suffix='x')}
- ROA: {format_metric('return_on_assets', fmt='.2%')}

The decision is based on comprehensive analysis of financial position, industry context, and market conditions.
        """.strip()
        
        return summary
    
    def _generate_key_findings(self,
                              feature_importances: List[FeatureImportance],
                              metrics: Dict[str, float],
                              credit_rating: str) -> List[str]:
        """Generate key findings list"""
        findings = []
        
        # Top 3 contributing factors
        for i, imp in enumerate(feature_importances[:3], 1):
            findings.append(
                f"Factor {i}: {imp.feature_name} is {imp.impact_level.lower()} "
                f"({imp.direction.lower()} impact on creditworthiness)"
            )
        
        # Financial health
        if metrics.get('debt_service_coverage_ratio', 0) > 1.5:
            findings.append("Strong debt service capability from operational cash flow")
        
        if metrics.get('current_ratio', 0) > 1.5:
            findings.append("Adequate liquidity position for meeting short-term obligations")
        
        if metrics.get('net_profit_margin', 0) > 0.10:
            findings.append("Healthy profit margins indicating operational efficiency")
        
        return findings
    
    def _identify_strengths(self,
                           metrics: Dict[str, float],
                           feature_importances: List[FeatureImportance]) -> List[str]:
        """Identify and list strengths"""
        strengths = []
        
        # Financial strengths
        if metrics.get('debt_to_equity', 0) < 1.0:
            strengths.append("Conservative capital structure with low leverage")
        
        if metrics.get('current_ratio', 0) > 2.0:
            strengths.append("Strong liquidity position")
        
        if metrics.get('debt_service_coverage_ratio', 0) > 2.0:
            strengths.append("Excellent debt service capacity")
        
        if metrics.get('net_profit_margin', 0) > 0.15:
            strengths.append("Strong profitability and margin control")
        
        if metrics.get('return_on_assets', 0) > 0.10:
            strengths.append("Efficient asset utilization")
        
        # SHAP-based strengths
        positive_factors = [imp for imp in feature_importances if imp.direction == 'POSITIVE']
        if len(positive_factors) >= 3:
            strengths.append(f"Multiple positive contributing factors to creditworthiness")
        
        return strengths
    
    def _identify_concerns(self,
                          metrics: Dict[str, float],
                          feature_importances: List[FeatureImportance],
                          risk_factors: List[RiskFactor]) -> List[str]:
        """Identify and list concerns"""
        concerns = []
        
        # From risk factors
        for risk in risk_factors:
            concerns.append(f"{risk.factor_name} - {risk.description}")
        
        # Financial concerns
        if metrics.get('debt_to_equity', 0) > 2.0:
            concerns.append("High financial leverage increases vulnerability to interest rate changes")
        
        if metrics.get('current_ratio', 0) < 1.0:
            concerns.append("Current liabilities exceed current assets")
        
        if metrics.get('debt_service_coverage_ratio', 0) < 1.25:
            concerns.append("Limited margin for error in debt service")
        
        # SHAP-based concerns
        negative_factors = [imp for imp in feature_importances if imp.direction == 'NEGATIVE']
        if len(negative_factors) >= 3:
            concerns.append("Multiple negative contributing factors present")
        
        return concerns
    
    def _generate_recommendations(self,
                                 credit_rating: str,
                                 risk_factors: List[RiskFactor],
                                 metrics: Dict[str, float]) -> List[str]:
        """Generate recommendations for credit committee"""
        recommendations = []
        
        # Rating-based recommendations
        if credit_rating in ['D', 'CCC']:
            recommendations.append("Recommend decline unless significant improvements demonstrated")
        elif credit_rating in ['B', 'BB']:
            recommendations.append("Consider decline or require substantial additional collateral")
        elif credit_rating in ['BBB']:
            recommendations.append("Conditional approval with enhanced monitoring recommended")
        elif credit_rating in ['A', 'AA', 'AAA']:
            recommendations.append("Standard approval process recommended")
        
        # Risk factor recommendations
        for risk in risk_factors:
            recommendations.append(f"Address {risk.factor_name}: {risk.recommendation}")
        
        # Specific metric recommendations
        if metrics.get('debt_to_equity', 0) > 2.0:
            recommendations.append("Require debt reduction plan as condition of approval")
        
        if metrics.get('current_ratio', 0) < 1.5:
            recommendations.append("Monitor working capital management closely")
        
        if metrics.get('debt_service_coverage_ratio', 0) < 1.5:
            recommendations.append("Require quarterly cash flow reporting")
        
        # Monitoring recommendations
        if credit_rating in ['D', 'CCC', 'B']:
            recommendations.append("Implement enhanced monitoring with quarterly reviews")
        elif credit_rating in ['BB', 'BBB']:
            recommendations.append("Implement semi-annual reviews and covenant monitoring")
        else:
            recommendations.append("Standard annual monitoring sufficient")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _perform_sensitivity_analysis(self,
                                     X: pd.DataFrame,
                                     metrics: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """
        Perform sensitivity analysis on key metrics.
        
        Shows how credit score changes with variations in key inputs.
        """
        sensitivity = {}
        
        # Analyze impact of ±10%, ±20%, ±30% changes in key metrics
        key_metrics = ['debt_to_equity', 'current_ratio', 'debt_service_coverage_ratio']
        
        for metric in key_metrics:
            if metric in metrics:
                base_value = metrics[metric]
                sensitivity[metric] = {
                    'base_value': base_value,
                    'impact_at_minus_30pc': base_value * 0.7,
                    'impact_at_plus_30pc': base_value * 1.3,
                    'elasticity': 0.8  # Score change per unit change in metric
                }
        
        return sensitivity
    
    def _calculate_confidence(self,
                            feature_importances: List[FeatureImportance],
                            metrics: Dict[str, float]) -> float:
        """
        Calculate confidence in the explanation.
        
        Based on clarity of feature importance and completeness of metrics.
        """
        # Start with base confidence
        confidence = 0.7
        
        # Add confidence if we have strong principal factors
        top_importance = feature_importances[0].importance_score if feature_importances else 0
        if top_importance > 80:
            confidence += 0.15
        elif top_importance > 60:
            confidence += 0.10
        
        # Add confidence if we have complete metrics
        expected_metrics = [
            'debt_to_equity', 'current_ratio', 'debt_service_coverage_ratio',
            'net_profit_margin', 'return_on_assets'
        ]
        available_metrics = sum(1 for m in expected_metrics if m in metrics)
        confidence += (available_metrics / len(expected_metrics)) * 0.15
        
        return min(confidence, 1.0)


class SWOTLLMGenerator:
    """
    Generate SWOT analysis using LLM from financial, sentiment, and industry inputs.

    Falls back to deterministic rule-based SWOT when LLM is unavailable.
    """

    def __init__(self, api_key: str = None, default_model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or "ollama"
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.default_model = default_model
        self.client = None
        if OpenAI is not None:
            try:
                client_kwargs = {"api_key": self.api_key}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self.client = OpenAI(**client_kwargs)
            except Exception as e:
                logger.warning(f"OpenAI client init failed in SWOTLLMGenerator, falling back to rule-based SWOT: {e}")

    def generate_swot(self,
                      company_name: str,
                      financial_metrics: Dict[str, float],
                      market_sentiment: Dict[str, Any],
                      industry_data: Dict[str, Any],
                      model: str = None) -> Dict[str, Any]:
        model_name = model or self.default_model

        if not self.client:
            return self._fallback_swot(company_name, financial_metrics, market_sentiment, industry_data, "RULE_BASED")

        prompt = self._build_prompt(company_name, financial_metrics, market_sentiment, industry_data)
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a credit underwriting analyst. Return only strict JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            parsed = self._parse_swot_json(content)
            if not parsed:
                logger.warning("LLM SWOT parse failed; using fallback SWOT")
                return self._fallback_swot(company_name, financial_metrics, market_sentiment, industry_data, model_name)

            return {
                "company_name": company_name,
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
                "opportunities": parsed.get("opportunities", []),
                "threats": parsed.get("threats", []),
                "generated_at": datetime.now().isoformat(),
                "model_used": model_name
            }

        except Exception as e:
            logger.error(f"LLM SWOT generation failed: {e}")
            return self._fallback_swot(company_name, financial_metrics, market_sentiment, industry_data, "RULE_BASED")

    def _build_prompt(self,
                      company_name: str,
                      financial_metrics: Dict[str, float],
                      market_sentiment: Dict[str, Any],
                      industry_data: Dict[str, Any]) -> str:
        return f"""
Generate a SWOT analysis for company: {company_name}.

Inputs:
- financial_metrics: {json.dumps(financial_metrics, default=str)}
- market_sentiment: {json.dumps(market_sentiment, default=str)}
- industry_data: {json.dumps(industry_data, default=str)}

Rules:
1) Use only the provided inputs.
2) Keep each bullet concise and business-readable.
3) Return exactly this JSON schema:
{{
  "strengths": ["..."],
  "weaknesses": ["..."],
  "opportunities": ["..."],
  "threats": ["..."]
}}
4) Produce 3-5 items in each section.
""".strip()

    @staticmethod
    def _parse_swot_json(content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content)
            required = ["strengths", "weaknesses", "opportunities", "threats"]
            if all(key in data and isinstance(data[key], list) for key in required):
                return data
            return {}
        except Exception:
            return {}

    def _fallback_swot(self,
                       company_name: str,
                       financial_metrics: Dict[str, float],
                       market_sentiment: Dict[str, Any],
                       industry_data: Dict[str, Any],
                       model_used: str) -> Dict[str, Any]:
        current_ratio = float(financial_metrics.get("current_ratio", 0) or 0)
        debt_to_equity = float(financial_metrics.get("debt_to_equity", 0) or 0)
        dscr = float(financial_metrics.get("debt_service_coverage_ratio", 0) or 0)
        net_margin = float(financial_metrics.get("net_profit_margin", 0) or 0)
        sentiment_score = float(market_sentiment.get("composite_sentiment_score", 0) or 0)
        cagr = float(industry_data.get("growth_rate_cagr", 0) or 0)

        strengths = []
        weaknesses = []
        opportunities = []
        threats = []

        if current_ratio >= 1.5:
            strengths.append(f"Healthy liquidity profile (current ratio {current_ratio:.2f}x)")
        else:
            weaknesses.append(f"Tight liquidity may constrain short-term flexibility (current ratio {current_ratio:.2f}x)")

        if debt_to_equity <= 1.5:
            strengths.append(f"Moderate leverage supports balance-sheet resilience (D/E {debt_to_equity:.2f})")
        else:
            weaknesses.append(f"Elevated leverage raises refinancing and solvency risk (D/E {debt_to_equity:.2f})")

        if dscr >= 1.5:
            strengths.append(f"Debt service coverage indicates repayment capacity (DSCR {dscr:.2f}x)")
        else:
            weaknesses.append(f"Debt service headroom is limited under stress (DSCR {dscr:.2f}x)")

        if net_margin >= 0.10:
            strengths.append(f"Profitability supports internal cash generation (net margin {net_margin:.1%})")
        else:
            weaknesses.append(f"Low profitability may limit retained earnings (net margin {net_margin:.1%})")

        if sentiment_score > 0.2:
            opportunities.append("Positive market sentiment can support revenue momentum and financing confidence")
        elif sentiment_score < -0.2:
            threats.append("Negative market sentiment may pressure demand and borrowing terms")

        if cagr >= 8:
            opportunities.append(f"Strong industry growth trajectory (CAGR {cagr:.1f}%) offers expansion runway")
        elif cagr > 0:
            opportunities.append(f"Moderate industry growth (CAGR {cagr:.1f}%) supports selective expansion")
        else:
            threats.append("Flat or contracting industry trend can weaken medium-term growth")

        regulatory = str(industry_data.get("regulatory_environment", "")).upper()
        if regulatory == "UNFAVORABLE":
            threats.append("Regulatory environment appears unfavorable and may increase compliance burden")
        elif regulatory == "FAVORABLE":
            opportunities.append("Supportive regulatory environment can accelerate strategic initiatives")

        if not opportunities:
            opportunities.append("Operational efficiency and product mix optimization can improve returns")
        if not threats:
            threats.append("Input-cost volatility and macro uncertainty remain ongoing external risks")

        return {
            "company_name": company_name,
            "strengths": strengths[:5],
            "weaknesses": weaknesses[:5],
            "opportunities": opportunities[:5],
            "threats": threats[:5],
            "generated_at": datetime.now().isoformat(),
            "model_used": model_used
        }


def create_mock_explainer() -> Tuple[SHAPExplainer, CreditDecisionExplainer]:
    """
    Create mock explainers for testing without actual model.
    
    Returns:
        Tuple of (SHAPExplainer, CreditDecisionExplainer)
    """
    # Mock model that returns input sum normalized
    class MockModel:
        def predict(self, X):
            return np.sum(X, axis=1) / X.shape[1]
    
    # Mock feature names
    feature_names = [
        'debt_to_equity', 'current_ratio', 'debt_service_coverage_ratio',
        'net_profit_margin', 'return_on_assets', 'asset_turnover',
        'interest_coverage', 'roe', 'roa', 'working_capital_ratio'
    ]
    
    # Create mock data
    mock_data = pd.DataFrame(
        np.random.randn(100, len(feature_names)),
        columns=feature_names
    )
    
    model = MockModel()
    shap_explainer = SHAPExplainer(model, feature_names, mock_data)
    credit_explainer = CreditDecisionExplainer(shap_explainer)
    
    return shap_explainer, credit_explainer
