
from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.orm import Session
from app.crud import settlement
from app.database import get_db
from app.crud.auth import get_current_user
from app.models import orm_models
from app.schemas import response
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.dependencies import get_member_in_pool

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/settle_up", tags=["Settlement"])


@router.get("/settle", response_model=response.SettlementResponse)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def get_loan_settlement(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(orm_models.Member).filter(
        orm_models.Member.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(403, "Not part of any pool")

    result = settlement.calculate_loan_settlement(db, member.pool_id)

    return response.SettlementResponse(
        success=True,
        message="Loan settlement calculated",
        status_code=200,
        data=result
    )