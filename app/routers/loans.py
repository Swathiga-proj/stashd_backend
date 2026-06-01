from fastapi import APIRouter, Depends, HTTPException,Query
from sqlalchemy.orm import Session
from app.crud import loan as loan_crud
from app.schemas import response,loan
from app.database import get_db
from app.crud.auth import get_current_user
from app.models import orm_models

router = APIRouter(prefix="/transactions",tags=["Summary"])




@router.post("/loans_list", response_model=response.LoanListResponse)
async def get_all_loans(
    data: loan.LoanListItem,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get All Loans in the Pool with Pagination
    """
    member = db.query(orm_models.Member).filter(
        orm_models.Member.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="You are not part of any pool")

    # Optional: Only allow Admin to see all loans
    # if member.role != "admin":
    #     raise HTTPException(status_code=403, detail="Only admin can view all loans")

    result = loan_crud.get_all_loans_in_pool(
        db=db,
        pool_id=member.pool_id,
        limit=data.limit,
        skip=data.skip
    )

    return response.LoanListResponse(
        success=True,
        message="Loans fetched successfully",
        status_code=200,
        data=result["loans"],
        total_given=result["total_given"],
        total_repaid=result["total_repaid"],
        outstanding=result["outstanding"],
        total=result["total"],           # Total count for pagination
        has_more=result["has_more"]
    )