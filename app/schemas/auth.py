from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ====================== AUTH ======================
class UserLogin(BaseModel):
    phone_number: str = Field(..., example="+91 9876543210")
    password: str = Field(..., example="demo123")


class UserCreate(BaseModel):
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        example="Priya Sharma"
    )
    
    phone_number: str = Field(
        ..., 
        example="+91 9876543210",
        description="Phone number with country code"
    )
    
    password: str = Field(
        ..., 
        min_length=6,
        max_length=100,
        example="demo123"
    )
    
    confirm_password: str = Field(
        ..., 
        example="demo123"
    )










