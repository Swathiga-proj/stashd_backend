from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from app.crud import transaction as curd_trn
from app.database import get_db
from app.crud.auth import get_current_user
from app.models import orm_models
from typing import Optional,Literal
from app.schemas import response,transaction
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.logger import logger
from app.dependencies import get_member_in_pool

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/income", response_model=response.TransactionResponse, status_code=201)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def add_income(
    data: transaction.MoneyInCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get user's member record in pool
    member = get_member_in_pool(pool_id=data.pool_id,current_user=current_user,db=db)


    if not member:
        raise HTTPException(403, "You are not part of any pool")

    txn = curd_trn.create_income(db, member.pool_id, data.model_dump())
    logger.info("income added to pool")
    return response.TransactionResponse(
        success=True,
        message="Income added successfully",
        status_code=status.HTTP_201_CREATED,
        data={"transaction_id": txn.id, "status": txn.status}
    )


@router.post("/expense", response_model=response.TransactionResponse, status_code=201)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def add_expense(
    data: transaction.ExpenseCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = get_member_in_pool(pool_id=data.pool_id,current_user=current_user,db=db)

    

    txn = curd_trn.create_expense(db, member.pool_id, data.model_dump())
    logger.info("expense added to pool")
    return response.TransactionResponse(
        success=True,
        message="Expense added successfully",
        status_code=status.HTTP_201_CREATED,
        data={"transaction_id": txn.id, "status": txn.status}
    )


@router.post("/loan", response_model=response.TransactionResponse, status_code=201)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def add_loan(
    data: transaction.LoanGivenCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = get_member_in_pool(pool_id=data.pool_id,current_user=current_user,db=db)

    txn = curd_trn.create_loan_given(db, member.pool_id, data.model_dump())
    logger.info("loan given out of pool")
    return response.TransactionResponse(
        success=True,
        message="Loan recorded successfully (Pending Approval)",
        status_code=status.HTTP_201_CREATED,
        data={"transaction_id": txn["transaction_id"],
              "loan_id":txn["loan_id"], "status": txn["status"]}
    )


@router.post("/repayment", response_model=response.TransactionResponse, status_code=201)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def add_repayment(
    data: transaction.RepaymentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = get_member_in_pool(pool_id=data.pool_id,current_user=current_user,db=db)


    repayment_data = data.model_dump()

    # Inject the member context fields so your database base model can read them if needed
    repayment_data['belongs_to_member_id'] = member.id
#  Explicitly provide the member.id or pass it as a keyword argument
    txn = curd_trn.create_repayment(
        db=db, 
        pool_id=member.pool_id, 
        # member_id=member.id, 
        data=repayment_data
    )    
    logger.info("repayment addded to pool")
    return response.TransactionResponse(
        success=True,
        message="Repayment recorded successfully (Pending Approval)",
        status_code=status.HTTP_201_CREATED,
        data={"transaction_id": txn["transaction_id"],
              "loan_id": txn["loan_id"],
                "status": txn["status"]}
    )

@router.post("/transaction_list", response_model=response.TransactionListResponse)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def get_transaction_list(
    data: transaction.TransactionListRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Transaction List for Activity Screen with Pagination
    """
    # Get user's pool membership
    member = get_member_in_pool(pool_id=data.pool_id,current_user=current_user,db=db)


    if not member:
        raise HTTPException(status_code=403, detail="You are not part of any pool")

    # Determine filters based on input
    
    transaction_type_filter = None if data.t_type == "all" else data.t_type
    status_filter = data.status  # None means all statuses

    # Role-based restrictions
    if member.role == "viewer":
        status_filter = "approved"  # Viewers can only see approved transactions

    result = curd_trn.get_transaction_list(
        db=db,
        pool_id=member.pool_id,
        transaction_type=transaction_type_filter,
        status=status_filter,
        limit=data.limit,
        skip=data.skip
    )

    # Convert to response format
    transactions = []
    for txn in result["transactions"]:
        transactions.append({
            "id": txn.id,
            "amount": txn.amount,
            "transaction_type": txn.transaction_type,
            "category": txn.category,
            "direction": txn.direction,
            "status": txn.status,
            "note": txn.note,
            "member_name": txn.member.nickname if txn.member else "Unknown",
            "created_at": txn.created_at
        })
    logger.info(f"transactions list fetched: {len(transactions)}")
    return response.TransactionListResponse(
        success=True,
        message="Transactions fetched successfully",
        status_code=200,
        data=transactions,
        total=result["total"],
        has_more=result["has_more"]
    )

@router.get("/dashboard", response_model=response.DashboardResponse)
# @limiter.limit("60/minute")  # Max 1 request per second average
async def get_dashboard(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(orm_models.Member).filter(
        orm_models.Member.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not part of any pool")

    summary = curd_trn.get_dashboard_summary(db, member.pool_id)

    # return response.DashboardResponse(
    #     success=True,
    #     message="Dashboard fetched successfully",
    #     status_code=200,
    #     data=summary
    # )
    return {
    "success": True,
    "message": "Dashboard fetched successfully",
    "status_code": 200,
    "data": summary
}
