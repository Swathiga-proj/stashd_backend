from fastapi import APIRouter,Depends,HTTPException,status,Request
from app.schemas import auth,response
from app.crud import auth as crud_auth
from sqlalchemy.orm import session
from app.database import get_db
from app.models import orm_models
from app.logger import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
import time
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post('/login', response_model=response.LoginResponse)
@limiter.limit("5/minute")  # Max 5 login attempts per minute per IP

async def login(request: Request,
          data:auth.UserLogin,
          db:session=Depends(get_db)):
    logger.info(f"Login attempt for phone: {data.phone_number}")
    user = crud_auth.authenticate_user(db, data.phone_number, data.password)
    time.sleep(2)
    if not user:
        logger.warning(f"Failed login attempt for phone: {data.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    access_token = crud_auth.create_access_token(data={"sub": str(user.id)})
    refresh_token = crud_auth.create_refresh_token(data={"sub": str(user.id)})
    logger.info(f"Login successful for user_id: {user.id}")
    return response.LoginResponse(
        success=True,
        message="Login successful",
        status_code=200,
        data={
            "access_token": access_token,
            "refresh_token":refresh_token,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name
        }
    )

# @router.post("/signup", response_model=response.SignupResponse, status_code=status.HTTP_201_CREATED)
# @limiter.limit("5/minute")  # Max 1 request per second average
# async def signup(request: Request,
#                 data: auth.UserCreate,
#                 db: session = Depends(get_db)):
#     if data.password != data.confirm_password:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Passwords do not match"
#         )
#     # Call the crud function
#     user = crud_auth.create_user(
#         db=db,
#         phone=data.phone_number,
#         password=data.password,
#         name=data.name
#     )
#     token = crud_auth.create_access_token(data={"sub": str(user.id)})
#     time.sleep(2)

#     return response.SignupResponse(
#         success=True,
#         message="Account created successfully",
#         status_code=status.HTTP_201_CREATED,
#         data={
#             "access_token": token,
#             "token_type": "bearer",
#             "user_id": user.id,
#             "name": user.name,
#             "phone_number": user.phone_number,
            
#         }
#     )

@router.post("/signup", response_model=response.SignupResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def signup(request: Request,
                data: auth.UserCreate,
                db: session = Depends(get_db)):
    try:
        if data.password != data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )

        user = crud_auth.create_user(
            db=db,
            phone=data.phone_number,
            password=data.password,
            name=data.name
        )
        token = crud_auth.create_access_token(data={"sub": str(user.id)})
        time.sleep(2)

        return response.SignupResponse(
            success=True,
            message="Account created successfully",
            status_code=status.HTTP_201_CREATED,
            data={
                "access_token": token,
                "token_type": "bearer",
                "user_id": user.id,
                "name": user.name,
                "phone_number": user.phone_number,
            }
        )

    except Exception as e:
        return {
            "success": False,
            "message": str(e),          
            "status_code": 500,
            "data": None
        }