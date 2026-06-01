
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from ..models import orm_models
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, UTC
import uuid


def record_settlement(
    db: Session,
    from_member_id: int,
    to_member_id: int,
    amount: float,
    note: str = None,
    current_member: orm_models.Member = None
):
    """Record a settlement with full transaction linkage"""
    
    if amount <= 0:
        raise HTTPException(400, "Settlement amount must be greater than zero")

    # Validate members belong to same pool
    from_member = db.query(orm_models.Member).filter_by(id=from_member_id).first()
    to_member = db.query(orm_models.Member).filter_by(id=to_member_id).first()

    if not from_member or not to_member:
        raise HTTPException(404, "Member not found")
    if from_member.pool_id != to_member.pool_id:
        raise HTTPException(400, "Members must belong to the same pool")

    # Create Settlement Record
    settlement = orm_models.Settlement(
        from_member_id=from_member_id,
        to_member_id=to_member_id,
        amount=amount,
        note=note or f"Settlement from {from_member.nickname} to {to_member.nickname}"
    )
    db.add(settlement)

    # Create Debit Transaction (from payer)
    debit_txn = orm_models.Transaction(
        amount=amount,
        transaction_type="transfer",
        direction="debit",
        member_id=from_member_id,
        pool_id=from_member.pool_id,
        note=f"Settlement paid to {to_member.nickname}",
        status="approved",
        approved_by_member_id=current_member.id if current_member else from_member_id,
        approved_at=datetime.now(UTC)
    )

    # Create Credit Transaction (to receiver)
    credit_txn = orm_models.Transaction(
        amount=amount,
        transaction_type="transfer",
        direction="credit",
        member_id=to_member_id,
        pool_id=to_member.pool_id,
        note=f"Settlement received from {from_member.nickname}",
        status="approved",
        approved_by_member_id=current_member.id if current_member else to_member_id,
        approved_at=datetime.now(UTC)
    )

    db.add_all([debit_txn, credit_txn])
    db.commit()

    return {
        "message": "Settlement recorded successfully",
        "settlement_id": settlement.id,
        "from": from_member.nickname,
        "to": to_member.nickname,
        "amount": amount,
        "transactions_created": 2
    }

def calculate_loan_settlement(db: Session, pool_id: int):
    """
    Calculate settlement based on Loans (who lent to whom)
    """
    # Get all loans in this pool
    loans = db.query(orm_models.Loan).filter(
        orm_models.Loan.lent_by_member_id.in_(
            db.query(orm_models.Member.id).filter(orm_models.Member.pool_id == pool_id)
        )
    ).all()

    # Calculate net position for each member
    balances = {}
    
    for loan in loans:
        # Calculate total repaid for this loan
        repaid = db.query(func.sum(orm_models.Repayment.amount)).filter(
            orm_models.Repayment.loan_id == loan.id
        ).scalar() or 0
        
        outstanding = loan.amount - repaid

        # Lender should receive
        if loan.lent_by_member_id not in balances:
            balances[loan.lent_by_member_id] = 0.0
        balances[loan.lent_by_member_id] += outstanding

        # Borrower should pay
        # Note: We need borrower_member_id. If you don't have it, we can use name only for now

    # Convert to list
    current_balances = []
    for member_id, balance in balances.items():
        member = db.query(orm_models.Member).filter(orm_models.Member.id == member_id).first()
        if member:
            current_balances.append({
                "member_id": member_id,
                "nickname": member.nickname,
                "balance": round(balance, 2),
                "to_receive": round(balance, 2) if balance > 0 else 0.0,
                "to_pay": round(abs(balance), 2) if balance < 0 else 0.0
            })

    # Minimal Transactions (Simple version for loans)
    minimal_transactions = []
    
    # Group by borrower (for simplicity)
    borrower_owes = {}
    for loan in loans:
        repaid = db.query(func.sum(orm_models.Repayment.amount)).filter(
            orm_models.Repayment.loan_id == loan.id
        ).scalar() or 0
        outstanding = loan.amount - repaid
        
        if outstanding > 0:
            if loan.borrower_name not in borrower_owes:
                borrower_owes[loan.borrower_name] = []
            borrower_owes[loan.borrower_name].append({
                "to_member_id": loan.lent_by_member_id,
                "to_member_name": loan.lent_by_member.nickname if loan.lent_by_member else "Unknown",
                "amount": outstanding
            })

    # Create minimal transactions
    for borrower_name, debts in borrower_owes.items():
        for debt in debts:
            minimal_transactions.append({
                "from_member_id": None,  # We don't have borrower_id yet
                "from_member_name": borrower_name,
                "to_member_id": debt["to_member_id"],
                "to_member_name": debt["to_member_name"],
                "amount": round(debt["amount"], 2)
            })

    return {
        "current_balances": current_balances,
        "minimal_transactions": minimal_transactions,
        "total_to_settle": sum(t["amount"] for t in minimal_transactions)
    }