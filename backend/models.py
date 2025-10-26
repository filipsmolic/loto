from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, ARRAY, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from database import Base


class Round(Base):
    __tablename__ = "rounds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    closed = Column(Boolean, default=False)
    results = Column(ARRAY(Integer), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tickets = relationship("Ticket", back_populates="round")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id"))
    owner_id = Column(String(20), nullable=False)
    numbers = Column(ARRAY(Integer), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    round = relationship("Round", back_populates="tickets")
