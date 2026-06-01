from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models import Transaction, Member
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, UTC
import uuid


def create_split_expense(
    db: Session,
    pool_id: int,
    paid_by_member_id: int,
    total_amount: float,
    category: str,
    note: str = None,
    split_details: list = None,          # [{"member_id": 1, "amount": 1400.0}, ...]
    current_member: Member = None
):
    if total_amount <= 0:
        raise HTTPException(400, "Total amount must be greater than zero")

    if not split_details or len(split_details) == 0:
        raise HTTPException(400, "Split details cannot be empty")

    total = Decimal(str(total_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    split_sum = Decimal('0')
    processed_splits = []

    # Step 1: Round each person's share to 2 decimal places
    for split in split_details:
        member_id = split['member_id']
        raw_amount = Decimal(str(split.get('amount', 0)))
        rounded_amount = raw_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        processed_splits.append({
            "member_id": member_id,
            "amount": float(rounded_amount)
        })
        split_sum += rounded_amount

    # Step 2: Adjust the last person to make total exact (Standard Banking Practice)
    difference = total - split_sum
    if difference != 0 and processed_splits:
        # Add/subtract the difference to the last member
        last_split = processed_splits[-1]
        last_split['amount'] = float(Decimal(str(last_split['amount'])) + difference)

    # Step 3: Final validation
    final_sum = sum(Decimal(str(s['amount'])) for s in processed_splits)
    if abs(final_sum - total) > Decimal('0.001'):
        raise HTTPException(400, "Could not reconcile split amounts")

    # ====================== CREATE TRANSACTIONS ======================
    split_group_id = str(uuid.uuid4())
    transactions = []

    for split in processed_splits:
        txn = Transaction(
            amount=split['amount'],
            transaction_type="expense",
            direction="debit",
            category=category,
            note=note or f"Split expense - {category}",
            member_id=split['member_id'],
            pool_id=pool_id,
            is_split=True,
            split_group_id=split_group_id,
            split_details=processed_splits,
            status="approved" if current_member and current_member.role == "admin" else "pending",
            approved_by_member_id=current_member.id if current_member and current_member.role == "admin" else None,
            approved_at=datetime.now(UTC) if current_member and current_member.role == "admin" else None,
            created_at=datetime.now(UTC)
        )
        transactions.append(txn)

    db.add_all(transactions)
    db.commit()

    return {
        "message": "Split expense recorded successfully with automatic rounding",
        "split_group_id": split_group_id,
        "total_amount": float(total),
        "transactions_count": len(transactions),
        "status": "approved" if current_member and current_member.role == "admin" else "pending",
        "note": "Last member's amount adjusted for exact total"
    }