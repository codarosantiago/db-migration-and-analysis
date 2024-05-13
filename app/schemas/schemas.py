from pydantic import BaseModel
from datetime import datetime

class EmployeeSchema(BaseModel):
    id: int
    name: str
    datetime: datetime
    department_id: int
    job_id: int

    class Config:
        orm_mode = True
