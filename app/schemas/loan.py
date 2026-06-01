from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ====================== LOAN ======================



# class LoanListItem(BaseModel):
#     id: int
#     amount: float
#     borrower_name: str
#     outstanding: float
#     is_settled: bool
#     created_at: datetime

class LoanListItem(BaseModel):
    skip: int
    limit: int
