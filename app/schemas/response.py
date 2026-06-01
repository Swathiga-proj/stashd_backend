from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
from .member import MemberCreate

# ====================== BASE RESPONSE ======================
class BaseResponse(BaseModel):
    success: bool = True
    message: str
    status_code: int = 200
    data: Optional[Any] = None


# ====================== AUTH ======================
class LoginResponse(BaseResponse):
    message: str = "Login successful"
    status_code: int = 200
    data: dict


class SignupResponse(BaseResponse):
    message: str = "Account created successfully"
    status_code: int = 201
    data: dict


# ====================== POOL & MEMBER ======================
class PoolCreateResponse(BaseResponse):
    message: str = "Pool created successfully"
    status_code: int = 201
    data: dict


class MemberAddResponse(BaseResponse):
    message: str = "Member added successfully"
    status_code: int = 201
    data: dict

class MemberResponse(BaseModel):
    id: int
    nickname: str
    phone_number: Optional[str] = None
    role: str
    color: str
    joined_at: datetime

class MembersListResponse(BaseModel):
    success: bool = True
    message: str = "Members fetched successfully"
    status_code: int = 200
    data: List[MemberResponse]
    total: int
    has_more: bool = True   # Optional

# ====================== TRANSACTION ======================
class TransactionResponse(BaseResponse):
    message: str = "Transaction recorded successfully"
    status_code: int = 201
    data: dict


class TransactionListResponse(BaseResponse):
    message: str = "Transactions fetched successfully"
    status_code: int = 200
    data: List[dict]
    total:int
    has_more:bool


class SplitExpenseResponse(BaseResponse):
    message: str = "Split expense recorded successfully"
    status_code: int = 201
    data: dict


# ====================== LOAN ======================
class LoanListResponse(BaseResponse):
    message: str = "Loans fetched successfully"
    status_code: int = 200
    data: List[dict]


# ====================== SETTLEMENT ======================
class SettlementResponse(BaseResponse):
    
    message: str = "Settlement processed successfully"
    status_code: int = 200
    data: dict


# ====================== DASHBOARD ======================
class DashboardResponse(BaseResponse):
    message: str = "Dashboard data fetched successfully"
    status_code: int = 200
    data: dict


# ====================== ERROR RESPONSE ======================
class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    status_code: int
    error: Optional[str] = None