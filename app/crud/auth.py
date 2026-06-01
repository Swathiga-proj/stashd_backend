from sqlalchemy.orm import Session
from fastapi import HTTPException,status,Depends
from app.models import orm_models
# from passlib.context import CryptContext
import bcrypt
from datetime import timedelta,datetime,UTC
from typing import Optional
from jose import JWTError,jwt
from fastapi.security import OAuth2PasswordBearer
from app.database import get_db

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SECRET_KEY = "your-super-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def authenticate_user(db: Session, phone_number: str, plain_password: str):
    user = db.query(orm_models.User).filter(orm_models.User.phone_number == phone_number).first()

    if not user:
        return None

    if not verify_password(plain_password, user.password_hashed):
        return None

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
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
    except JWTError:
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