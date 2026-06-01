from fastapi import APIRouter,Depends,HTTPException,status
from app.schemas import auth,response
from app.crud import auth as crud_auth
from sqlalchemy.orm import session
from app.database import get_db
from app.models import orm_models

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post('/login', response_model=response.LoginResponse)
def login(data:auth.UserLogin,db:session=Depends(get_db)):
    user = crud_auth.authenticate_user(db, data.phone_number, data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    token = crud_auth.create_access_token(data={"sub": str(user.id)})
    
    return response.LoginResponse(
        success=True,
        message="Login successful",
        status_code=200,
        data={
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name
        }
    )

@router.post("/signup", response_model=response.SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: auth.UserCreate, db: session = Depends(get_db)):
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    # Call the crud function
    user = crud_auth.create_user(
        db=db,
        phone=data.phone_number,
        password=data.password,
        name=data.name
    )
    token = crud_auth.create_access_token(data={"sub": str(user.id)})


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
