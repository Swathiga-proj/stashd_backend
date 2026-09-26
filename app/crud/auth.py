from sqlalchemy.orm import Session
from fastapi import HTTPException,status,Depends
from app.models import orm_models
# from passlib.context import CryptContext
import bcrypt
import os
from datetime import timedelta,datetime,UTC
from typing import Optional
from jose import JWTError,jwt
from fastapi.security import OAuth2PasswordBearer
from app.database import get_db
from app.logger import logger
import uuid
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")  # default to HS256 if not setACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_MINUTES = os.environ.get("REFRESH_TOKEN_EXPIRE_MINUTES")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    #encode-decode
    #str  →  .encode()  →  bytes   (going into bcrypt)
    #bytes  →  .decode()  →  str   (coming out, going into DB)


def authenticate_user(db: Session, phone_number: str, plain_password: str):
    try:
        user = db.query(orm_models.User).filter(orm_models.User.phone_number == phone_number).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        if not verify_password(plain_password, user.password_hashed):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return user
    except HTTPException:
        raise  
    except Exception as e:
        logger.error(f"Error authenticating user {phone_number}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):

    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire,"jti": str(uuid.uuid4()),"type":"access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):

    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire,"jti": str(uuid.uuid4()),"type":"refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        print(user_id)
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        logger.error(f"Error in getting current user={e}")
        raise credentials_exception

    user = db.query(orm_models.User).filter(orm_models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def check_phone_exists(phone:str,db:Session=Depends(get_db)):
    phone = db.query(orm_models.User).filter(orm_models.User.phone_number==phone).first()

    if not phone:
        return None
    
    return True if phone else False
def create_user(phone:str,name:str,password:str,db:Session=Depends(get_db)):
    user = db.query(orm_models.User).filter(orm_models.User.phone_number==phone).first()
    if user:
        logger.error(f"Phone number already registered:{phone}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    hash_pass = get_password_hash(password=password)

    new_user = orm_models.User(
        name=name,
        phone_number=phone,
        password_hashed=hash_pass,
        is_verified=False,         
        created_at=datetime.now(UTC)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user