from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models import orm_models
from datetime import datetime, UTC
from typing import Optional,Dict
from sqlalchemy import desc,func

def create_transaction(
    db: Session, 
    pool_id: int,
    member_id: int,
    amount: float,
    transaction_type: str,
    note: str = None,
    category: str = None,
    commit: bool = True,
    **extra
):
    """General function to create transaction"""
    member = db.query(orm_models.Member).filter(
        orm_models.Member.id == member_id
    ).first()
    if not member:
        raise ValueError(f"Member not found for user_id: {member_id}")

    status = "approved" if member.role == "admin" else "pending"
    transaction = orm_models.Transaction(
        amount=amount,
        transaction_type=transaction_type,
        direction="credit" if transaction_type in ["income", "repayment"] else "debit",
        note=note,
        category=category,
        member_id=member_id,
        pool_id=pool_id,
        status=status,           # Important: goes to pending for approval
        created_at=datetime.now(UTC),
        **extra
    )
    
    db.add(transaction)
    if commit:
        db.commit()
        db.refresh(transaction)
    return transaction


def create_income(db: Session, pool_id: int, data: dict):
    return create_transaction(
        db=db,
        pool_id=pool_id,
        member_id=data['belongs_to_member_id'],
        amount=data['amount'],
        transaction_type="income",
        note=data.get('note'),
        category=data.get('category')
    )


def create_expense(db: Session, pool_id: int, data: dict):
    return create_transaction(
        db=db,
        pool_id=pool_id,
        member_id=data['belongs_to_member_id'],
        amount=data['amount'],
        transaction_type="expense",
        note=data.get('note'),
        category=data.get('category')
        )


def create_loan_given(db: Session, pool_id: int, data: dict):
    txn = create_transaction(
        db=db,
        pool_id=pool_id,
        member_id=data['belongs_to_member_id'],
        amount=data['amount'],
        transaction_type="loan_given",
        note=data.get('note'),
        commit=False
    )
    
    # Create loan record
    loan = orm_models.Loan(
        amount=data['amount'],
        borrower_name=data['lent_to_name'],
        lent_by_member_id=data['belongs_to_member_id'],
        note=data.get('note'),
        created_at=datetime.now(UTC)
    )
    db.add(loan)
    db.commit()
    return {
        "transaction_id": txn.id,
        "loan_id": loan.id,
        "amount": loan.amount,
        "borrower_name": loan.borrower_name,
        "status":txn.status
    }


def create_repayment(db: Session, pool_id: int, data: dict):
    loan_id = data.get('loan_id')

    loan = db.query(orm_models.Loan).filter(orm_models.Loan.id == loan_id).first()
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
        # 1. Create the Repayment record
    repayment = orm_models.Repayment(
        amount=data['amount'],
        loan_id=loan_id,
        payment_method=data.get('payment_method'),
        note=data.get('note')
    )
    db.add(repayment)
    db.flush()  # writes the row + makes it visible to the sum query below, without committing yet

    # 2. Recompute total repaid for this loan and update is_settled
    total_repaid = db.query(func.sum(orm_models.Repayment.amount)).filter(
        orm_models.Repayment.loan_id == loan_id
    ).scalar() or 0

    loan.is_settled = total_repaid >= loan.amount
    db.add(loan)


        # 1. Create the Repayment record (tracks loan-specific repayment info)
    repayment = orm_models.Repayment(
        amount=data['amount'],
        loan_id=data.get('loan_id'),
        payment_method=data.get('payment_method'),
        note=data.get('note')
    )
    db.add(repayment)
    db.commit()
    db.refresh(repayment)

    # 2. Create the Transaction record (ledger entry, links back via reference_id)
    txn_result = create_transaction(
        db=db,
        pool_id=pool_id,
        member_id=data.get('belongs_to_member_id'),
        amount=data['amount'],
        transaction_type="repayment",
        note=data.get('note'),
        reference_type="repayment",
        reference_id=repayment.id
    )
    # 3. Return combined info 
    return {
        "transaction_id": txn_result.id,
        "loan_id": repayment.loan_id,
        "status": txn_result.status
    }

def get_transaction_list(
    db: Session,
    pool_id: int,
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    skip: int = 0
    ) -> Dict:
        """
        Get transactions with pagination
        """
        query = db.query(orm_models.Transaction).filter(
            orm_models.Transaction.pool_id == pool_id
        )

        # Apply filters
        if transaction_type:
            query = query.filter(orm_models.Transaction.transaction_type == transaction_type)

        if status:
            query = query.filter(orm_models.Transaction.status == status)

        # Order by latest first
        query = query.order_by(desc(orm_models.Transaction.created_at))

        # Get total count
        total = query.count()

        # Get paginated data
        transactions = query.offset(skip).limit(limit).all()

        return {
            "transactions": transactions,
            "total": total,
            "has_more": (skip + limit) < total
        }
def get_dashboard_summary(
        db: Session, 
        pool_id: int):
    """
    Get dashboard summary for a pool
    """
    # Get pool balance
    balance = db.query(orm_models.PoolBalance).filter(
        orm_models.PoolBalance.pool_id == pool_id
    ).first()

    # # Get total loans given
    total_loans_given = db.query(func.sum(orm_models.Loan.amount)).join(orm_models.Member,orm_models.Loan.lent_by_member_id==orm_models.Member.id)\
    .filter(orm_models.Member.pool_id==pool_id).scalar() or 0.0
    

    return {
        "total_balance": round(balance.total_balance if balance else 0.0, 2),
        "total_income": round(balance.total_income if balance else 0.0, 2),
        "total_expense": round(balance.total_expense if balance else 0.0, 2),
        "total_loans_given": round(total_loans_given, 2)
    }