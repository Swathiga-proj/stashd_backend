from fastapi import FastAPI
from app.routers import auth,loans,pools,settlement,transactions
from app.models import events  # Import to register listeners
from app.models import orm_models
from app.database import Base, engine


Base.metadata.create_all(bind=engine)  # creates missing tables, skips existing ones

app = FastAPI(title="Stashd API")


app.include_router(auth.router)
app.include_router(loans.router)
app.include_router(pools.router)
app.include_router(settlement.router)
app.include_router(transactions.router)


@app.get("/")
def root():
    return {"message": "Stashd is running"}