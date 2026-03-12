from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.config import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    document_type = Column(String, nullable=False)  # e.g., "invoice", "bankStatement", "financialReport"
    file_path = Column(String, nullable=False)  # MinIO object path
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, nullable=False)  # User ID
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String, nullable=False)
    version = Column(Integer, default=1)  # for versioning
    is_latest = Column(String, default="true")  # "true" or "false"
    document_metadata = Column("metadata", Text, nullable=True)  # JSON metadata
    
    # Relationships
    financial_metrics = relationship("FinancialMetrics", back_populates="document")

    class Config:
        from_attributes = True
