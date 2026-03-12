from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database.config import Base


class EntityOwnership(Base):
    __tablename__ = "entity_ownerships"
    __table_args__ = (
        UniqueConstraint("entity_id", "user_id", name="uq_entity_owner"),
    )

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class Config:
        from_attributes = True