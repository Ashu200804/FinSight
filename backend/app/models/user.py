from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.database.config import Base
import enum

class UserRole(str, enum.Enum):
    CREDIT_ANALYST = "credit_analyst"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CREDIT_ANALYST, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class Config:
        from_attributes = True
