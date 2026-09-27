from sqlalchemy.orm import Session
from fastapi import HTTPException,status,Depends
from app.models import orm_models
from datetime import timedelta,datetime,UTC
from typing import Optional
from app.database import get_db
from app.crud import auth
from app.logger import logger

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

def add_member_to_pool(
    pool_id: int,
    name: str,
    phone: str,
    color: str,
    password: str,
    role: str,
    db: Session = Depends(get_db)          # Fixed: proper dependency injection
):
    """Add a new member to an existing pool."""

    # Check if pool exists
    pool = db.query(orm_models.Pool).filter(orm_models.Pool.id == pool_id).first()
    if not pool:
        logger.error(f"Pool not found: pool_id={pool_id}")
        raise HTTPException(status_code=404, detail="Pool not found")

    # Check if phone number already registered
    existing_user = db.query(orm_models.User).filter(
        orm_models.User.phone_number == phone
    ).first()

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
        logger.info(f"New user created: user_id={user.id}")
    else:
        user = existing_user
        logger.info(f"Using existing user: user_id={user.id}")

    # Create member – now uses the provided color instead of hard-coding
    member = orm_models.Member(
        nickname=name,
        color=color,                       # Fixed: use the parameter
        role=role,
        pool_id=pool_id,
        user_id=user.id
    )

    db.add(member)
    db.commit()
    db.refresh(member)
    logger.info(f"Member created: member_id={member.id}, pool_id={pool_id}")

    return member



from sqlalchemy.orm import joinedload

def get_pool_members(
    db: Session, 
    pool_id: int,
    limit: int = 20,
    skip: int = 0
):
    """
    Get members in a pool with pagination.
    Uses joinedload to avoid N+1 queries.
    """
    query = (
        db.query(orm_models.Member)
        .options(joinedload(orm_models.Member.user))   
        .filter(orm_models.Member.pool_id == pool_id)
        .order_by(orm_models.Member.id)
    )

    total = query.count()
    members = query.offset(skip).limit(limit).all()

    logger.info(f"Fetched {len(members)} members out of total={total} for pool_id={pool_id}")

    member_list = [
        {
            "id": member.id,
            "nickname": member.nickname,
            "phone_number": member.user.phone_number if member.user else None,
            "role": member.role,
            "color": member.color,
            "joined_at": member.created_at
        }
        for member in members
    ]

    return {
        "members": member_list,
        "total": total,
        "has_more": (skip + limit) < total
    }