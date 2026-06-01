from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    password_hashed = Column(String, nullable=True)
    phone_number = Column(String, unique=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

    members = relationship("Member", back_populates="user")


class Pool(Base):
    __tablename__ = "pools"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(UTC))
    created_by_user_id = Column(Integer, nullable=False)
    members = relationship("Member", back_populates="pool", cascade="all, delete-orphan")


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    nickname = Column(String, nullable=False)
    color = Column(String, nullable=False)
    role = Column(String, default="member")          # admin, member, viewer

    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.now(UTC))

    pool = relationship("Pool", back_populates="members")
    user = relationship("User", back_populates="members")
    transactions = relationship("Transaction",
                                foreign_keys="[Transaction.member_id]", 
                                back_populates="member")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)   # income, expense, loan_given, repayment, transfer
    category = Column(String, nullable=True)
    direction = Column(String, nullable=False)          # credit / debit

    from_person = Column(String, nullable=True)
    to_person = Column(String, nullable=True)
    note = Column(String, nullable=True)

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)

    # Split support
    is_split = Column(Boolean, default=False)
    split_details = Column(JSON, nullable=True)

    # Approval Workflow
    status = Column(String, default="approved")         # pending, approved, rejected
    approved_by_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.now(UTC))

    member = relationship("Member", 
                          foreign_keys=[member_id],
                          back_populates="transactions")
    pool = relationship("Pool")
    approved_by = relationship("Member", foreign_keys=[approved_by_member_id])


class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    borrower_name = Column(String, nullable=False)
    lent_by_member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    note = Column(String, nullable=True)
    is_settled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(UTC))

    lent_by_member = relationship("Member", foreign_keys=[lent_by_member_id])
    repayments = relationship("Repayment", back_populates="loan", cascade="all, delete-orphan")


class Repayment(Base):
    __tablename__ = "repayments"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    payment_method = Column(String, nullable=True)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))

    loan = relationship("Loan", back_populates="repayments")


# ====================== SUMMARY / BALANCE ======================
class PoolBalance(Base):
    """Daily or cached balance summary for fast UI loading"""
    __tablename__ = "pool_balances"

    id = Column(Integer, primary_key=True)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False, unique=True)

    total_balance = Column(Float, default=0.0)
    total_income = Column(Float, default=0.0)
    total_expense = Column(Float, default=0.0)
    loans_outstanding = Column(Float, default=0.0)

    last_updated = Column(DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    pool = relationship("Pool")


# Optional: Settlement History
class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True)
    from_member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    to_member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    amount = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(UTC))

    from_member = relationship("Member", foreign_keys=[from_member_id])
    to_member = relationship("Member", foreign_keys=[to_member_id])