"""SQLAlchemy model for persisting extraction review results."""

from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from app.database.config import Base


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    metrics_id = Column(Integer, ForeignKey("financial_metrics.id"), nullable=True)

    # AI-extracted data: nested JSON keyed by section -> field -> {value, label, unit, confidence}
    extracted_fields = Column(JSON, nullable=False, default={})

    # Human-corrected values: nested JSON keyed by section -> field -> corrected_value
    corrected_fields = Column(JSON, nullable=True)

    # Reviewer metadata
    review_notes = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending | approved | rejected
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    entity = relationship("Entity", backref="extraction_results")

    def __repr__(self):
        return f"<ExtractionResult(id={self.id}, entity_id={self.entity_id}, status={self.status})>"
