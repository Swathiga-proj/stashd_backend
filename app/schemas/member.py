from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime



# ====================== MEMBER ======================
class MemberCreate(BaseModel):
    pool_id: int 
    name: str = Field(..., example="Father-in-law")
    phone_number: str = Field(..., example="+91 9876543210")
    password: str = Field(..., min_length=6)
    role: str = Field("member", example="member")  # admin, member, viewer

class MemberList(BaseModel):
    limit: int = 10
    skip: int = 0
