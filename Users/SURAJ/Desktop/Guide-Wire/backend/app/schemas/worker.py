from datetime import datetime
from pydantic import BaseModel


class WorkerCreate(BaseModel):
    name: str
    platform: str
    zone: str
    working_hours: str


class WorkerOut(WorkerCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
