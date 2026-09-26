
from sqlalchemy.orm import Session
from fastapi import HTTPException,status,Depends
from ..models import orm_models
from sqlalchemy import desc,func
from ..database import get_db



def get_all_loans_in_pool(db: Session, pool_id: int,limit: int = 10,
    skip: int = 0):
    """
    Get ALL loans given by any member in the pool
    """

    query = db.query(orm_models.Loan)\
    .join(orm_models.Loan.lent_by_member)\
    .filter(orm_models.Member.pool_id == pool_id)\
    .order_by(desc(orm_models.Loan.created_at))\


    total = query.count()
    loans = query.offset(skip).limit(limit).all()

    total_given = 0
    total_repaid = 0
    outstanding = 0
    loan_list : list[dict] = []

    for l in loans:
        # Calculate repaid amount for this loan
        repaid = db.query(func.sum(orm_models.Repayment.amount)).filter(
            orm_models.Repayment.loan_id == l.id
        ).scalar() or 0

        out = l.amount - repaid

        total_given += l.amount
        total_repaid += repaid
        outstanding += out

        loan_list.append({
            "id": l.id,
            "amount": l.amount,
            "borrower_name": l.borrower_name,
            "lent_by_member": l.lent_by_member.nickname if l.lent_by_member else "Unknown",
            "outstanding": round(out, 2),
            "is_settled": repaid >= l.amount,
            "note": l.note,
            "created_at": l.created_at
        })

    return {
            "loans": loan_list,
            "total": total,              
            "total_given": round(total_given, 2),
            "total_repaid": round(total_repaid, 2),
            "outstanding": round(outstanding, 2),
            "has_more": (skip + limit) < total 
        }