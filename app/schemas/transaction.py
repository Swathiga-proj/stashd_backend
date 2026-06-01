from pydantic import BaseModel, Field
from typing import List, Optional,Literal
from datetime import datetime



# ====================== TRANSACTION ======================
class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0)
    note: Optional[str] = None
    date: Optional[datetime] = None


class MoneyInCreate(TransactionBase):
    transaction_type: str = "income"
    belongs_to_member_id: int
    category: Optional[str] = None


class ExpenseCreate(TransactionBase):
    transaction_type: str = "expense"
    belongs_to_member_id: int
    category: str = Field(..., example="Groceries")


class LoanGivenCreate(TransactionBase):
    transaction_type: str = "loan_given"
    lent_to_name: str = Field(..., example="Husband")
    lent_to_member_id:int 
    belongs_to_member_id: int  # who is giving the loan


class RepaymentCreate(TransactionBase):
    transaction_type: str = "repayment"
    loan_id: int
    payment_method: str = Field(..., example="UPI")

# schemas/transaction.py
class TransactionListRequest(BaseModel):
    t_type: Literal["all", "income", "expense", "loan_given", "repayment"] = "all"
    status: Optional[Literal["pending", "approved", "rejected"]] = None
    limit: int = 10
    skip: int = 0

