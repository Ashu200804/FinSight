"""Database models for CAM reports history."""

from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.config import Base


class CAMReport(Base):
    __tablename__ = "cam_reports"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    credit_score = Column(Float, nullable=True)
    risk_category = Column(String(50), nullable=True)
    approval_probability = Column(Float, nullable=True)  # 0-1
    report_path = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    entity = relationship("Entity", backref="cam_reports")
