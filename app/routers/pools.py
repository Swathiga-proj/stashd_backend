from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from app.crud import pools as crud_mem
from app.schemas import pools, response
from app.database import get_db
from app.crud.auth import get_current_user
from app.models import orm_models
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.logger import logger
from app.dependencies import get_member_in_pool
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/pools", tags=["Pools"])


@router.post("/create_pool", response_model=response.PoolCreateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("8/minute")
async def create_pool(
    data: pools.PoolCreate,

    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pool = crud_mem.create_pool(data.name, current_user.id,db)
    logger.info(f"pool created:{pool.id}")
    
    return response.PoolCreateResponse(
        success=True,
        message="Pool created successfully",
        status_code=status.HTTP_201_CREATED,
        data={
            "pool_id": pool.id,
            "name": pool.name
        }
    )

@router.post("/add_member", response_model=response.MemberAddResponse, status_code=201)
# @limiter.limit("60/minute")
async def add_member(
    data: pools.MemberCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # print("Userid=",current_user.id)
    # Check if current user is admin of this pool
    member = get_member_in_pool(pool_id=data.pool_id,current_user=current_user,db=db)
    
    if not member or member.role != "admin":
        raise HTTPException(status_code=403, detail="Only pool admin can add members")

    new_member = crud_mem.add_member_to_pool(
        db=db,
        pool_id=data.pool_id,
        color=data.color,
        name=data.name,
        phone=data.phone_number,
        password=data.password,
        role=data.role
    )
    logger.info(f"new member added to pool:{new_member}")
    
    return {
        "success": True,
        "message": "Member added successfully",
        "status_code": status.HTTP_201_CREATED,
        "data": {
            "member_id": new_member.id,
            "nickname": new_member.nickname,
            "role": new_member.role
        }
    }    

@router.post("/members", response_model=response.MembersListResponse)
# @limiter.limit("60/minute")
async def get_members(
    data : pools.MemberList,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Members List with Pagination
    """
    member = get_member_in_pool(pool_id=data.pool_id,current_user=current_user,db=db)

    if not member:
        logger.error("You are not part of any pool")
        raise HTTPException(status_code=403, detail="You are not part of any pool")

    result = crud_mem.get_pool_members(
        db=db,
        pool_id=member.pool_id,
        limit=data.limit,
        skip=data.skip
    )

    return response.MembersListResponse(
        success=True,
        message="Members list fetched successfully",
        status_code=200,
        data=result["members"],
        total=result["total"],
        has_more=result["has_more"]
    )
    