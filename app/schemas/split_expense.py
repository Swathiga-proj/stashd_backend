from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime




# Split Expense
class SplitDetail(BaseModel):
    member_id: int
    amount: float

class SplitExpenseCreate(BaseModel):
    total_amount: float
    category: str
    note: Optional[str] = None
    split_details: List[SplitDetail]

class SplitExpenseResponse(BaseModel):
    success: bool = True
    message: str = "Split expense recorded successfully"
    status_code: int = 201
    data: dict