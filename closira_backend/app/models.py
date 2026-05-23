from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, index=True)
    customer_name = Column(String)
    message = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sop_matched = Column(String, nullable=True)
    suggested_response = Column(String, nullable=True)
    escalation_reason = Column(String, nullable=True)

    history = relationship("History", back_populates="enquiry")

class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    enquiry_id = Column(Integer, ForeignKey("enquiries.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)
    details = Column(JSON)

    enquiry = relationship("Enquiry", back_populates="history")
