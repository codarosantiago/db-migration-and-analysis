from fastapi import FastAPI, File, UploadFile, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import pandas as pd
from io import StringIO
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from sqlalchemy import inspect
import logging
from dateutil.parser import parse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# Load environment variables from .env file
load_dotenv()

POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
if POSTGRES_PASSWORD is None:
    raise ValueError("Environment variable POSTGRES_PASSWORD is not set")

app = FastAPI()

# Database connection setup
DATABASE_URL = f"postgresql://fastapi:{POSTGRES_PASSWORD}@db/mydatabase"
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise HTTPException(status_code=500, detail="Database connection failed")

Base = declarative_base()

# Models
class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    datetime = Column(String)
    department_id = Column(Integer)
    job_id = Column(Integer)

    class Config:
        orm_mode = True

class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String)

    class Config:
        orm_mode = True

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, index=True)
    job = Column(String)

    class Config:
        orm_mode = True

# Pydantic schemas
class EmployeeSchema(BaseModel):
    id: int
    name: str
    datetime: datetime
    department_id: int
    job_id: int

    class Config:
        orm_mode = True


def init_db():
    Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    init_db()



@app.post("/upload-csv/{table_name}")
async def upload_csv(table_name: str, file: UploadFile = File(...)):
    # Define model mapping to their corresponding SQLAlchemy models
    model_mapping = {
        'employees': Employee,
        'departments': Department,
        'jobs': Job
    }

    if table_name not in model_mapping:
        raise HTTPException(status_code=400, detail="Invalid table name provided.")

    # Get the model based on table_name
    model = model_mapping[table_name]

    # Get column names from the model
    headers = [column.name for column in inspect(model).columns]

    # Read the CSV file into a DataFrame with the correct headers
    csv_file_content = StringIO(str(file.file.read(), 'utf-8'))
    chunk_size = 1000  # Define the chunk size for batch processing

    # Create a new session for the transaction
    session = SessionLocal()

    try:
        # Process the CSV in chunks
        for chunk in pd.read_csv(csv_file_content, header=None, names=headers, chunksize=chunk_size):

            # Validate and convert datetime format for employees
            if table_name == 'employees':
                chunk['datetime'] = chunk['datetime'].apply(lambda x: parse(x).isoformat() if pd.notnull(x) else None)
                # Allow 'name' and 'datetime' to be null, remove the dropna
                chunk['name'] = chunk['name'].where(pd.notnull(chunk['name']), None)

            # Replace NaN with default values
            if 'job_id' in chunk.columns:
                chunk['job_id'] = chunk['job_id'].fillna(0).astype(int)
            if 'department_id' in chunk.columns:
                chunk['department_id'] = chunk['department_id'].fillna(0).astype(int)

            # Use the session for the transaction
            session.execute(
                model.__table__.insert(),
                chunk.to_dict(orient='records')
            )
            session.commit()  # Commit after each chunk

        return {"message": f"Data uploaded successfully to {table_name}"}
    except Exception as e:
        session.rollback()  # Rollback in case of error
        logger.error(f"Error uploading data to {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()  # Ensure the session is closed after operation

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


