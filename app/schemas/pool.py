from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime



# ====================== POOL ======================
class PoolCreate(BaseModel):
    name: str = Field(..., example="Family Stash")

