from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.config import Base


class CreditScore(Base):
    """
    Stores final credit scores and underwriting decisions.
    Links to Entity and FinancialMetrics for historical tracking and decision audit.
    """
    __tablename__ = "credit_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, unique=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    metrics_id = Column(Integer, ForeignKey("financial_metrics.id"), nullable=True)
    
    # Credit Score Results
    credit_score = Column(Integer, nullable=False)  # 300-1000
    probability_of_default = Column(Float, nullable=False)  # Percentage
    risk_category = Column(String(50), nullable=False)  # EXCELLENT, VERY_GOOD, GOOD, FAIR, POOR, VERY_POOR, UNACCEPTABLE
    
    # Component Scores (for detailed analysis)
    financial_strength_score = Column(Float, nullable=True)  # 0-100
    bank_relationship_score = Column(Float, nullable=True)  # 0-100
    industry_risk_score = Column(Float, nullable=True)  # 0-100
    management_quality_score = Column(Float, nullable=True)  # 0-100
    collateral_strength_score = Column(Float, nullable=True)  # 0-100
    legal_risk_score = Column(Float, nullable=True)  # 0-100
    fraud_risk_score = Column(Float, nullable=True)  # 0-100
    credit_bureau_score = Column(Float, nullable=True)  # 0-100
    
    # Detailed scoring factors (JSON)
    component_scores_json = Column(JSON, nullable=True)
    risk_drivers_json = Column(JSON, nullable=True)
    scoring_factors_json = Column(JSON, nullable=True)
    
    # Credit Decision
    financial_grade = Column(String(10), nullable=True)  # AAA, AA, A, BBB, BB, B, CCC, D (future)
    decision = Column(String(100), nullable=True)  # APPROVED, DECLINED, APPROVED_WITH_CONDITIONS
    decision_rationale = Column(Text, nullable=True)
    recommended_conditions = Column(JSON, nullable=True)
    recommended_rate_adjustment = Column(Integer, nullable=True)  # Basis points
    
    # Approval Tracking
    approval_status = Column(String(50), default='pending')  # pending, approved, rejected, review
    approval_notes = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # User ID who approved
    
    # Audit Fields
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    entity = relationship("Entity", back_populates="credit_score")
    document = relationship("Document")
    financial_metrics = relationship("FinancialMetrics")
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<CreditScore(id={self.id}, entity={self.entity_id}, score={self.credit_score}, risk={self.risk_category})>"


class CreditScoringHistory(Base):
    """
    Historical tracking of credit scores for trend analysis.
    Allows monitoring of credit quality changes over time.
    """
    __tablename__ = "credit_scoring_history"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    credit_score = Column(Integer, nullable=False)
    probability_of_default = Column(Float, nullable=False)
    risk_category = Column(String(50), nullable=False)
    
    # Trend tracking
    score_change = Column(Float, nullable=True)  # Change from previous score
    trend = Column(String(50), nullable=True)  # improving, deteriorating, stable
    
    # Snapshot of key metrics at time of assessment
    financial_strength_snapshot = Column(Float, nullable=True)
    bank_relationship_snapshot = Column(Float, nullable=True)
    industry_risk_snapshot = Column(Float, nullable=True)
    management_quality_snapshot = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CreditScoringHistory(entity={self.entity_id}, score={self.credit_score}, trend={self.trend})>"


class UnderwritingDecision(Base):
    """
    Formal underwriting decision record for audit and compliance.
    Tracks approval chain and decision justification.
    """
    __tablename__ = "underwriting_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_score_id = Column(Integer, ForeignKey("credit_scores.id"), nullable=False, unique=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    
    # Decision Details
    decision = Column(String(100), nullable=False)  # APPROVED, DECLINED, PENDING_REVIEW, APPROVED_WITH_CONDITIONS
    decision_reason = Column(Text, nullable=False)
    
    # Approval Chain
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Credit manager review
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Final approver
    
    # Conditions and Monitoring
    approval_conditions = Column(JSON, nullable=True)  # List of conditions
    monitoring_requirements = Column(JSON, nullable=True)  # List of monitoring requirements
    review_frequency = Column(String(50), nullable=True)  # monthly, quarterly, annual, on_demand
    
    # Rate and Terms
    proposed_interest_rate = Column(Float, nullable=True)  # Annual rate %
    proposed_loan_amount = Column(Float, nullable=True)  # ₹
    proposed_tenure = Column(Integer, nullable=True)  # Months
    proposed_collateral_requirement = Column(Float, nullable=True)  # % of loan
    
    # Timeline
    decision_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    decision_expiry = Column(DateTime, nullable=True)  # When decision expires
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    credit_score_rel = relationship("CreditScore", foreign_keys=[credit_score_id])
    entity_rel = relationship("Entity")
    explanation = relationship("ExplanationModel", back_populates="credit_decision", uselist=False)
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<UnderwritingDecision(id={self.id}, entity={self.entity_id}, decision={self.decision})>"
