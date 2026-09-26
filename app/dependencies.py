from app.models import orm_models
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException,status

def get_member_in_pool(pool_id: int, current_user, db: Session) -> orm_models.Member:
    member = db.query(orm_models.Member).filter(
        orm_models.Member.user_id == current_user.id,
        orm_models.Member.pool_id == pool_id
    ).first()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this pool"
        )
    return member