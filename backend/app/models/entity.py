from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.config import Base
import enum

class LoanType(str, enum.Enum):
    TERM_LOAN = "term_loan"
    WORKING_CAPITAL = "working_capital"
    EQUIPMENT_FINANCE = "equipment_finance"
    INVOICE_DISCOUNTING = "invoice_discounting"

class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    
    # Company Details
    company_name = Column(String, nullable=False)
    cin = Column(String, unique=True, nullable=False, index=True)
    pan = Column(String, unique=True, nullable=False, index=True)
    sector = Column(String, nullable=False)
    subsector = Column(String, nullable=False)
    turnover = Column(Float, nullable=True)
    address = Column(Text, nullable=False)
    
    # Loan Details
    loan_type = Column(Enum(LoanType), nullable=True)
    loan_amount = Column(Float, nullable=True)
    tenure = Column(Integer, nullable=True)  # in months
    interest_rate = Column(Float, nullable=True)
    purpose_of_loan = Column(Text, nullable=True)
    
    # Metadata
    is_draft = Column(String, default="true")  # "true" or "false"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    financial_metrics_list = relationship("FinancialMetrics", back_populates="entity")
    credit_score = relationship("CreditScore", back_populates="entity", uselist=False)
    explanations = relationship("ExplanationModel", back_populates="entity")

    class Config:
        from_attributes = True
