from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


# ====================== AUTH ======================
class UserLogin(BaseModel):
    phone_number: str 
    password: str 

    model_config = ConfigDict(
        json_schema_extra = {
            "examples": [
                {
                    "phone_number": "+919876543210",
                    "password": "demo123"
                }
            ]
        }
    )



class UserCreate(BaseModel):
    name: str
    
    phone_number: str 
    
    password: str 
    
    confirm_password: str 

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Priya Sharma",
                    "phone_number": "+91 9876543210",
                    "password": "demo123",
                    "confirm_password": "demo123"
                }
            ],
            # If you want to force string length constraints at the schema level
            "properties": {
                "name": {"minLength": 2, "maxLength": 100},
                "password": {"minLength": 6, "maxLength": 100}
            }
        }
    )










