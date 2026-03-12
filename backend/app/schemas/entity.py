from pydantic import BaseModel, Field
from app.models.entity import LoanType
from datetime import datetime
from typing import Optional

class CompanyDetails(BaseModel):
    company_name: str
    cin: str
    pan: str
    sector: str
    subsector: str
    turnover: Optional[float] = None
    address: str

class LoanDetails(BaseModel):
    loan_type: Optional[LoanType] = None
    loan_amount: Optional[float] = None
    tenure: Optional[int] = None  # in months
    interest_rate: Optional[float] = None
    purpose_of_loan: Optional[str] = None

class EntityCreate(BaseModel):
    company_details: Optional[CompanyDetails] = None
    loan_details: Optional[LoanDetails] = None
    is_draft: bool = True

class EntityUpdate(BaseModel):
    company_details: Optional[CompanyDetails] = None
    loan_details: Optional[LoanDetails] = None
    is_draft: bool = True

class EntityResponse(BaseModel):
    id: int
    company_name: str
    cin: str
    pan: str
    sector: str
    subsector: str
    turnover: Optional[float]
    address: str
    loan_type: Optional[LoanType]
    loan_amount: Optional[float]
    tenure: Optional[int]
    interest_rate: Optional[float]
    purpose_of_loan: Optional[str]
    is_draft: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EntityDraftResponse(BaseModel):
    id: int
    company_name: Optional[str]
    cin: Optional[str]
    pan: Optional[str]
    sector: Optional[str]
    subsector: Optional[str]
    turnover: Optional[float]
    address: Optional[str]
    loan_type: Optional[LoanType]
    loan_amount: Optional[float]
    tenure: Optional[int]
    interest_rate: Optional[float]
    purpose_of_loan: Optional[str]
    is_draft: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
