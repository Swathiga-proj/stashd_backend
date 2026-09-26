from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime




# ====================== SETTLEMENT ======================
class SettlementBalance(BaseModel):
    member_id: int
    nickname: str
    balance: float
    to_receive: float = 0.0
    to_pay: float = 0.0
    pool_id: int
class MinimalTransaction(BaseModel):
    from_member_id: int
    from_member_name: str
    to_member_id: int
    to_member_name: str
    amount: float
    pool_id: int
class SettlementResponse(BaseModel):
    success: bool = True
    message: str = "Settlement calculated"
    status_code: int = 200
    current_balances: List[SettlementBalance]
    minimal_transactions: List[MinimalTransaction]  # from, to, amount
    pool_id: int