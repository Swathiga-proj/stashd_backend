from pydantic import BaseModel, Field,ConfigDict
from typing import List, Optional
from datetime import datetime



# ====================== POOL ======================
class PoolCreate(BaseModel):
    name: str

    model_config = ConfigDict(
    json_schema_extra={
     "examples": [{
         "name" : "Family Stash"}]
    })

# ====================== MEMBER ======================
class MemberCreate(BaseModel):
    pool_id: int 
    name: str 
    phone_number: str 
    password: str 
    role: str   # admin, member, viewer
    model_config = ConfigDict(
    json_schema_extra={
     "examples": [{
         "name" : "Father-in-law",
         "phone_number":"+91 9876543210",
         "password":"demo123",
         "role":"admin"}],

         "properties":{
             "password": {"minLength": 6, "maxLength": 100}
         }
         })

class MemberList(BaseModel):
    limit: int = 10
    skip: int = 0
    pool_id:int
