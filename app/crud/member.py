from sqlalchemy.orm import Session
from fastapi import HTTPException,status,Depends
from app.models import orm_models
from datetime import timedelta,datetime,UTC
from typing import Optional
from app.database import get_db
from app.crud import auth


def create_pool(pool_name: str,created_by_user_id: int,db:Session=Depends(get_db)):
    
    pool = orm_models.Pool(name=pool_name, 
                       created_by_user_id = created_by_user_id,
                       created_at=datetime.now(UTC))
    
    db.add(pool)
    db.commit()
    db.refresh(pool)

    # Add creator as Admin
    admin_member = orm_models.Member(
        nickname= "Admin",
        color="#6366f1",
        role="admin",
        pool_id=pool.id,
        user_id=created_by_user_id
    )
    db.add(admin_member)
    db.commit()

    return pool

def add_member_to_pool(pool_id:int,
                       name:str,
                       phone:str,
                       color:str,
                       password:str,
                       role:str,
                       db:Session=get_db):
    """Add new member to existing pool"""
    
    # Check if pool exists
    pool = db.query(orm_models.Pool).filter(orm_models.Pool.id == pool_id).first()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    # Check if phone number already registered
    existing_user = db.query(orm_models.User).filter(orm_models.User.phone_number == phone).first()

    user = None

    if not existing_user:
        # Create new user
        hashed_password = auth.get_password_hash(password)
        user = orm_models.User(
            name=name,
            phone_number=phone,
            password_hashed=hashed_password,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user = existing_user

    # Create member
    create_member = orm_models.Member(nickname=name,
                                  color="#14b8a6",
                                  role=role,
                                  pool_id=pool_id)
    
    db.add(create_member)
    db.commit()
    db.refresh(create_member)
    return create_member

def get_pool_members(
    db: Session, 
    pool_id: int,
    limit: int = 20,
    skip: int = 0
):
    """
    Get members in a pool with pagination
    """
    query = db.query(orm_models.Member).filter(
        orm_models.Member.pool_id == pool_id
    ).order_by(
        orm_models.Member.id,   # Admin first
    )

    total = query.count()
    members = query.offset(skip).limit(limit).all()
    print("total:", total)
    print("skip:", skip)
    print("limit:", limit)
    print("members:", members)
    member_list = []
    for member in members:
        member_list.append({
            "id": member.id,
            "nickname": member.nickname,
            "phone_number": member.user.phone_number if member.user else None,
            "role": member.role,
            "color": member.color,
            "joined_at": member.created_at
        })

    return {
        "members": member_list[:limit],
        "total": total,
        "has_more": (skip + limit) < total
    }