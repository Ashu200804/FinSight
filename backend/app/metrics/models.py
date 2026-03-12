from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.config import Base

class FinancialMetrics(Base):
    """
    Stores calculated financial metrics for a document.
    Links to Document and Entity for historical tracking.
    """
    __tablename__ = "financial_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    
    # Extracted financial metrics (JSON for flexibility)
    metrics_json = Column(JSON, nullable=False)
    
    # Key score summaries
    profitability_score = Column(Float, nullable=True)
    liquidity_score = Column(Float, nullable=True)
    solvency_score = Column(Float, nullable=True)
    efficiency_score = Column(Float, nullable=True)
    overall_health_score = Column(Float, nullable=True)
    
    # Detailed ratio calculations (JSON for comprehensive storage)
    ratios_json = Column(JSON, nullable=False)
    
    # Credit scoring inputs
    credit_score_inputs_json = Column(JSON, nullable=True)
    
    # Status
    calculation_status = Column(String(50), default='success')
    warnings = Column(JSON, nullable=True)
    errors = Column(JSON, nullable=True)
    
    # Audit fields
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="financial_metrics")
    entity = relationship("Entity", back_populates="financial_metrics_list")
    
    def __repr__(self):
        return f"<FinancialMetrics(id={self.id}, document_id={self.document_id}, entity_id={self.entity_id})>"
