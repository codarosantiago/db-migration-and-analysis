from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.utils.config import POSTGRES_PASSWORD, logger

DATABASE_URL = f"postgresql://fastapi:{POSTGRES_PASSWORD}@db/mydatabase"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
