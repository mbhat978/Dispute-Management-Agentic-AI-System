from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional

# Support both relative and absolute imports
try:
    from .database import Base
except ImportError:
    from database import Base


class LoanAccount(Base):
    __tablename__ = "loan_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    monthly_emi_amount: Mapped[float] = mapped_column(Float, nullable=False)
    total_outstanding: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="loan_accounts")

    def __repr__(self):
        return f"<LoanAccount(id={self.id}, customer_id={self.customer_id}, emi=${self.monthly_emi_amount})>"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_tier: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'Basic', 'Premium', 'Gold'
    current_account_balance: Mapped[float] = mapped_column(Float, nullable=False)
    card_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="**** **** **** 1234")
    card_status: Mapped[str] = mapped_column(String(20), nullable=False, default="Active")  # 'Active', 'Blocked'
    inactive_cards: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="[]")  # JSON list of old cards
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="amal.c.r@ibm.com")  # Email field added

    # Relationships
    transactions = relationship("Transaction", back_populates="customer")
    dispute_tickets = relationship("DisputeTicket", back_populates="customer")
    loan_accounts = relationship("LoanAccount", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', tier='{self.account_tier}', email='{self.email}')>"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    merchant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # 'success', 'failed', 'pending'
    is_international: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refunded_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), default="debit", nullable=False)  # 'debit' or 'credit'

    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    atm_logs = relationship("ATM_Log", back_populates="transaction")
    dispute_tickets = relationship("DisputeTicket", back_populates="transaction")

    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, status='{self.status}')>"


class ATM_Log(Base):
    __tablename__ = "atm_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=False)
    atm_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status_code: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., '200_DISPENSED', '500_HARDWARE_FAULT'

    # Relationships
    transaction = relationship("Transaction", back_populates="atm_logs")

    def __repr__(self):
        return f"<ATM_Log(id={self.id}, atm_id='{self.atm_id}', status='{self.status_code}')>"


class DisputeTicket(Base):
    __tablename__ = "dispute_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    dispute_reason: Mapped[str] = mapped_column(Text, nullable=False)
    dispute_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Category from triage: 'fraud', 'duplicate', 'atm_failure', etc.
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='open'
    )  # 'open', 'under_investigation', 'auto_approved', 'auto_rejected', 'human_review_required', 'pending_review'
    final_decision: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Final decision made by Decision Agent
    decision_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string containing decision reasoning
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="dispute_tickets")
    customer = relationship("Customer", back_populates="dispute_tickets")
    audit_logs = relationship("AuditLog", back_populates="ticket")

    def __repr__(self):
        return f"<DisputeTicket(id={self.id}, status='{self.status}', reason='{self.dispute_reason[:50]}...')>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("dispute_tickets.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(255), nullable=False)
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # 'thought', 'tool_call', 'observation', 'decision'
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = relationship("DisputeTicket", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, agent='{self.agent_name}', action='{self.action_type}')>"