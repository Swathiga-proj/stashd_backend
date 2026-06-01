from sqlalchemy import event
from sqlalchemy.orm import Session
from app.models.orm_models import Transaction, PoolBalance, Loan, Member
from datetime import datetime, UTC


# ============================================================
# 1. INCREMENTAL BALANCE UPDATE
# ============================================================
def update_balance_incremental(mapper, connection, target: Transaction):
    """Incrementally update pool balance"""
    if target.status != "approved":
        return

    session = Session.object_session(target)
    if not session:
        return

    pool_id = target.pool_id

    balance = session.query(PoolBalance).filter_by(pool_id=pool_id).first()
    if not balance:
        balance = PoolBalance(pool_id=pool_id)
        session.add(balance)

    amount = abs(target.amount)

    if target.direction == "credit":
        balance.total_income = (balance.total_income or 0.0) + amount
        balance.total_balance = (balance.total_balance or 0.0) + amount
    else:
        balance.total_expense = (balance.total_expense or 0.0) + amount
        balance.total_balance = (balance.total_balance or 0.0) - amount
        balance.last_updated = datetime.now(UTC)


# ============================================================
# 2. LOAN CREATION → AUTO DEBIT TRANSACTION
# ============================================================
def create_loan_debit_transaction(mapper, connection, target: Loan):
    """When a Loan is created, automatically create a debit transaction"""
    session = Session.object_session(target)
    if not session:
        return

    # Create debit transaction for the lender
    debit_txn = Transaction(
        amount=target.amount,
        transaction_type="loan_given",
        direction="debit",
        member_id=target.lent_by_member_id,
        pool_id=session.query(Member).filter_by(id=target.lent_by_member_id).first().pool_id,
        note=target.note or f"Loan given to {target.borrower_name}",
        status="approved",
        approved_by_member_id=target.lent_by_member_id,
        approved_at=datetime.now(UTC),
        created_at=datetime.now(UTC)
    )
    session.add(debit_txn)


# ============================================================
# 3. ADMIN APPROVAL → TRIGGER BALANCE UPDATE
# ============================================================
def on_transaction_approval(mapper, connection, target: Transaction):
    """When a pending transaction is approved by admin, update balance"""
    if target.status == "approved" and hasattr(target, '_previously_pending'):
        # Re-trigger balance update
        update_balance_incremental(mapper, connection, target)


# ============================================================
# REGISTER ALL EVENTS
# ============================================================
event.listen(Transaction, 'after_insert', update_balance_incremental)
event.listen(Transaction, 'after_update', update_balance_incremental)
event.listen(Transaction, 'after_delete', update_balance_incremental)

event.listen(Loan, 'after_insert', create_loan_debit_transaction)

# Approval trigger
event.listen(Transaction, 'after_update', on_transaction_approval)