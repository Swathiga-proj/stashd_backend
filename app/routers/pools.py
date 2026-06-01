from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.orm import Session
from app.crud import member as crud_mem
from app.schemas import response,pool,member
from app.database import get_db
from app.crud.auth import get_current_user
from app.models import orm_models

router = APIRouter(prefix="/pools", tags=["Pools"])


@router.post("/create_pool", response_model=response.PoolCreateResponse, status_code=201)
async def create_pool(
    data: pool.PoolCreate,

    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pool = crud_mem.create_pool(data.name, current_user.id,db)
    
    return response.PoolCreateResponse(
        success=True,
        message="Pool created successfully",
        status_code=201,
        data={
            "pool_id": pool.id,
            "name": pool.name
        }
    )


@router.post("/add_member", response_model=response.MemberAddResponse, status_code=201)
async def add_member(
    data: member.MemberCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # print("Userid=",current_user.id)
    # Check if current user is admin of this pool
    member = db.query(orm_models.Member).filter(
        orm_models.Member.user_id == current_user.id,
        orm_models.Member.pool_id == data.pool_id
    ).first()
    
    if not member or member.role != "admin":
        raise HTTPException(status_code=403, detail="Only pool admin can add members")

    new_member = crud_mem.add_member_to_pool(
        db=db,
        pool_id=data.pool_id,
        color="#ffffff",
        name=data.name,
        phone=data.phone_number,
        password=data.password,
        role=data.role
    )

    return response.MemberAddResponse(
        success=True,
        message="Member added successfully",
        status_code=201,
        data={
            "member_id": new_member.id,
            "nickname": new_member.nickname,
            "role": new_member.role
        }
    )

@router.post("/members", response_model=response.MembersListResponse)
async def get_members(
    data : member.MemberList,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Members List with Pagination
    """
    member = db.query(orm_models.Member).filter(
        orm_models.Member.user_id == current_user.id
    ).first()

    if not member:
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