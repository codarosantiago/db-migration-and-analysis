from fastapi import FastAPI, File, UploadFile, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
import pandas as pd
from io import StringIO
import datetime
import os
from dotenv import load_dotenv
from sqlalchemy import inspect

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
    app.logger.error(f"Failed to create database engine: {e}")
    raise HTTPException(status_code=500, detail="Database connection failed")

Base = declarative_base()

# Models
class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    datetime = Column(DateTime)
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
    datetime: datetime.datetime
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
    df = pd.read_csv(StringIO(str(file.file.read(), 'utf-8')), header=None, names=headers)
    
    # Convert 'datetime' for the 'employees' table
    if table_name == 'employees':
        df['datetime'] = pd.to_datetime(df['datetime'])

    try:
        # Insert data into the database
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        return {"message": f"Data uploaded successfully to {table_name}"}
    except Exception as e:
        app.logger.error(f"Error uploading data to {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


