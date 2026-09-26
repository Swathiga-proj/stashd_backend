


from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from app.crud import split_expense as crud_split
from app.database import get_db
from app.crud.auth import get_current_user
from app.models import orm_models
from app.schemas import response,split_expense
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


router = APIRouter(prefix="/transactions", tags=["split expense"])


@router.post("/split_expense", 
             response_model=response.SplitExpenseResponse, 
             status_code=status.HTTP_201_CREATED)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def add_split_expense(
    data: split_expense.SplitExpenseCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get current member
    current_member = db.query(orm_models.Member).filter(
        orm_models.Member.user_id == current_user.id
    ).first()

    if not current_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not part of any pool")

    # Validate all split member_ids belong to the same pool
    member_ids = [s.member_id for s in data.split_details]
    # TEMP DEBUG — add this if it's not already in your route
    all_members = db.query(orm_models.Member).filter(orm_models.Member.id.in_(member_ids)).all()
    for m in all_members:
        print(f"member.id={m.id}, member.pool_id={m.pool_id}, current_member.pool_id={current_member.pool_id}, current_member.id={current_member.id}")

    valid_members = db.query(orm_models.Member).filter(
        orm_models.Member.id.in_(member_ids),
        orm_models.Member.pool_id == current_member.pool_id
    ).count()

    valid_members = db.query(orm_models.Member).filter(
        orm_models.Member.id.in_(member_ids),
        orm_models.Member.pool_id == current_member.pool_id
    ).count()

    if valid_members != len(member_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some members don't belong to this pool")

    result = crud_split.create_split_expense(
        db=db,
        pool_id=current_member.pool_id,
        paid_by_member_id=current_member.id,
        total_amount=data.total_amount,
        category=data.category,
        note=data.note,
        split_details=[s.model_dump() for s in data.split_details],
        current_member=current_member
    )

    return response.SplitExpenseResponse(
        success=True,
        message=result["message"],
        status_code=status.HTTP_201_CREATED,
        data=result
    )