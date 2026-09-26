from sqlalchemy import create_engine,text
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,DeclarativeBase
from app.config import settings
import os
from app.logger import logger
from sqlalchemy.exc import SQLAlchemyError

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:poql@localhost:5432/stashd")

def create_database_if_not_exists():
    """Connect to default 'postgres' DB and create target DB if missing."""
    db_name = DATABASE_URL.split("/")[-1]
    base_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"

    temp_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    try:
        with temp_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name}
            ).fetchone()

            if not exists:
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                logger.info(f"Database '{db_name}' created successfully")
            else:
                logger.info(f"Database '{db_name}' already exists")
    except SQLAlchemyError as e:
        logger.error(f"Failed to check/create database '{db_name}': {e}")
        raise  
    finally:
        temp_engine.dispose()

create_database_if_not_exists()

# Dependency — use this in your routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()