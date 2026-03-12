"""
Database models for storing credit decision explanations.

Stores SHAP-based explanations, feature importance, and risk factors
for audit trail and future reference.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.config import Base


class ExplanationModel(Base):
    """Main explanation record for a credit decision"""
    __tablename__ = 'explanation_models'
    
    id = Column(Integer, primary_key=True)
    credit_decision_id = Column(Integer, ForeignKey('underwriting_decisions.id'), nullable=False)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    
    # Decision information
    decision = Column(String(50))  # APPROVE, CONDITIONAL_APPROVE, DECLINE
    credit_score = Column(Float)  # 0-1000
    credit_rating = Column(String(10))  # AAA-D
    decision_confidence = Column(Float)  # 0-1
    
    # Explanation components
    executive_summary = Column(Text)
    explanation_confidence = Column(Float)  # 0-1 confidence in explanation
    
    # SHAP data
    shap_values = Column(JSON)  # Feature-wise SHAP values
    base_value = Column(Float)  # SHAP's expected value
    feature_names = Column(JSON)  # List of feature names
    
    # Key findings and analysis
    key_findings = Column(JSON)  # List of key findings
    strengths = Column(JSON)  # List of strengths
    concerns = Column(JSON)  # List of concerns
    recommendations = Column(JSON)  # List of recommendations
    
    # Sensitivity data
    sensitivity_analysis = Column(JSON)  # How score changes with input changes
    
    # Model information
    model_version = Column(String(50))
    model_type = Column(String(50))  # e.g., 'xgboost', 'neural_network'
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))  # Analyst who generated
    
    # Relationships
    credit_decision = relationship('UnderwritingDecision', back_populates='explanation')
    entity = relationship('Entity', back_populates='explanations')
    feature_importances = relationship('FeatureImportanceModel', back_populates='explanation', cascade='all, delete-orphan')
    risk_factors = relationship('RiskFactorModel', back_populates='explanation', cascade='all, delete-orphan')
    user = relationship('User', foreign_keys=[created_by])
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'credit_decision_id': self.credit_decision_id,
            'entity_id': self.entity_id,
            'decision': self.decision,
            'credit_score': self.credit_score,
            'credit_rating': self.credit_rating,
            'decision_confidence': self.decision_confidence,
            'executive_summary': self.executive_summary,
            'explanation_confidence': self.explanation_confidence,
            'key_findings': self.key_findings,
            'strengths': self.strengths,
            'concerns': self.concerns,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FeatureImportanceModel(Base):
    """SHAP feature importance for each feature in the explanation"""
    __tablename__ = 'feature_importances'
    
    id = Column(Integer, primary_key=True)
    explanation_id = Column(Integer, ForeignKey('explanation_models.id'), nullable=False)
    
    # Feature information
    feature_name = Column(String(255), nullable=False)
    feature_value = Column(Float)  # Actual value in the input
    
    # SHAP analysis
    shap_value = Column(Float)  # Raw SHAP value
    importance_score = Column(Float)  # Normalized 0-100
    contribution_percentage = Column(Float)  # Percentage of total importance
    
    # Direction and impact
    direction = Column(String(50))  # POSITIVE, NEGATIVE, NEUTRAL
    impact_level = Column(String(50))  # CRITICAL, HIGH, MEDIUM, LOW
    
    # Interpretation
    interpretation = Column(Text)  # Human-readable interpretation
    
    # Ranking
    rank = Column(Integer)  # 1-indexed rank by importance
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    explanation = relationship('ExplanationModel', back_populates='feature_importances')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'feature_name': self.feature_name,
            'importance_score': self.importance_score,
            'direction': self.direction,
            'impact_level': self.impact_level,
            'shap_value': self.shap_value,
            'rank': self.rank
        }


class RiskFactorModel(Base):
    """Identified risk factors in the credit decision"""
    __tablename__ = 'risk_factors'
    
    id = Column(Integer, primary_key=True)
    explanation_id = Column(Integer, ForeignKey('explanation_models.id'), nullable=False)
    
    # Risk information
    factor_name = Column(String(255), nullable=False)
    category = Column(String(100))  # e.g., 'LEVERAGE', 'LIQUIDITY', 'PROFITABILITY', 'LEGAL'
    
    # Severity
    severity = Column(String(50))  # CRITICAL, HIGH, MEDIUM, LOW
    severity_score = Column(Float)  # 0-100
    
    # Description and recommendations
    description = Column(Text)
    recommendation = Column(Text, nullable=False)
    
    # Supporting data
    supporting_metrics = Column(JSON)  # Dict of metrics supporting this risk
    mitigating_factors = Column(JSON)  # List of mitigating factors if any
    
    # Impact assessment
    impact_on_decision = Column(String(50))  # How this affects the decision
    confidence = Column(Float)  # 0-1 confidence in risk assessment
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    explanation = relationship('ExplanationModel', back_populates='risk_factors')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'factor_name': self.factor_name,
            'category': self.category,
            'severity': self.severity,
            'description': self.description,
            'recommendation': self.recommendation,
            'supporting_metrics': self.supporting_metrics
        }


class FeatureImportanceCache(Base):
    """Cache feature importance values to avoid recalculation"""
    __tablename__ = 'feature_importance_cache'
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    
    # Cache key (hash of input features)
    cache_key = Column(String(255), unique=True, nullable=False)
    
    # Cached results
    shap_values = Column(JSON)
    feature_names = Column(JSON)
    base_value = Column(Float)
    
    # Expiry
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # TTL for cache
    
    # Relationships
    entity = relationship('Entity', foreign_keys=[entity_id])
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class ExplanationAuditLog(Base):
    """Audit trail for explanation generation"""
    __tablename__ = 'explanation_audit_logs'
    
    id = Column(Integer, primary_key=True)
    explanation_id = Column(Integer, ForeignKey('explanation_models.id'), nullable=False)
    
    # Action
    action = Column(String(100))  # CREATED, REVIEWED, APPROVED, REJECTED, MODIFIED
    action_by = Column(Integer, ForeignKey('users.id'))
    notes = Column(Text)
    
    # Comparison (for modifications)
    previous_decision = Column(String(50))
    new_decision = Column(String(50))
    
    # Metadata
    client_ip = Column(String(50))
    user_agent = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    explanation = relationship('ExplanationModel', foreign_keys=[explanation_id])
    user = relationship('User', foreign_keys=[action_by])


class ExplanationTemplate(Base):
    """Templates for explanation generation"""
    __tablename__ = 'explanation_templates'
    
    id = Column(Integer, primary_key=True)
    
    # Template info
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    rating_category = Column(String(50))  # e.g., 'AAA', 'BBB', 'D' or 'ALL'
    
    # Template content
    executive_summary_template = Column(Text)
    key_findings_template = Column(Text)
    strengths_template = Column(Text)
    concerns_template = Column(Text)
    recommendations_template = Column(Text)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher = more priority
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Association table for features in risk factors
feature_risk_association = Table(
    'feature_risk_association',
    Base.metadata,
    Column('risk_factor_id', Integer, ForeignKey('risk_factors.id')),
    Column('feature_importance_id', Integer, ForeignKey('feature_importances.id'))
)
