from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20))
    city = Column(String(100))
    total_orders = Column(Integer, default=0)
    total_spend = Column(Float, default=0.0)

    logs = relationship("CommunicationLog", back_populates="customer")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    rules = Column(Text, nullable=False)  # JSON string

    campaigns = relationship("Campaign", back_populates="segment")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    segment = relationship("Segment", back_populates="campaigns")
    logs = relationship("CommunicationLog", back_populates="campaign")


class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String(20), nullable=False)  # delivered, opened, clicked, failed
    timestamp = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="logs")
    customer = relationship("Customer", back_populates="logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    action = Column(String(200), nullable=False)
    detail = Column(String(500), default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
