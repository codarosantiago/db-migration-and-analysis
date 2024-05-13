from fastapi import APIRouter, File, UploadFile, HTTPException
from app.schemas.schemas import EmployeeSchema
from app.models.models import Employee, Department, Job
from app.utils.utils import parse_custom_date
from app.database import SessionLocal
from sqlalchemy import inspect
import pandas as pd
from io import StringIO
from dateutil.parser import parse

router = APIRouter()

@router.post("/upload-csv/{table_name}", response_model=dict)
async def upload_csv(table_name: str, file: UploadFile = File(...)):
    model_mapping = {
        'employees': Employee,
        'departments': Department,
        'jobs': Job
    }
    if table_name not in model_mapping:
        raise HTTPException(status_code=400, detail="Invalid table name provided.")

    model = model_mapping[table_name]
    headers = [column.name for column in inspect(model).columns]
    csv_file_content = StringIO(str(file.file.read(), 'utf-8'))
    chunk_size = 1000

    session = SessionLocal()

    try:
        for chunk in pd.read_csv(csv_file_content, header=None, names=headers, chunksize=chunk_size):
            
            if table_name == 'employees':
                chunk['datetime'] = chunk['datetime'].apply(lambda x: parse(x).isoformat() if pd.notnull(x) else None)
                # Allow 'name' and 'datetime' to be null, remove the dropna
                chunk['name'] = chunk['name'].where(pd.notnull(chunk['name']), None)

                # Replace NaN with default values
            if 'job_id' in chunk.columns:
                chunk['job_id'] = chunk['job_id'].fillna(0).astype(int)
            if 'department_id' in chunk.columns:
                chunk['department_id'] = chunk['department_id'].fillna(0).astype(int)

                
            session.execute(model.__table__.insert(), chunk.to_dict(orient='records'))
            session.commit()
        return {"message": f"Data uploaded successfully to {table_name}"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
