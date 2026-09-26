from fastapi import FastAPI
from app.routers import auth,loans,pools,settlement,transactions,split_expense
from app.models import events  # Import to register listeners
from app.models import orm_models
from app.database import Base, engine

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    global_exception_handler
)
from app.logger import logger

Base.metadata.create_all(bind=engine)  # creates missing tables, skips existing ones
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Stashd API",
              version="1.0.0")

# Register error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

logger.info("Stashd backend starting up...")


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(loans.router)
app.include_router(pools.router)
app.include_router(settlement.router)
app.include_router(transactions.router)
app.include_router(split_expense.router)

@app.get("/")
def root():
    return {"message": "Stashd is running"}