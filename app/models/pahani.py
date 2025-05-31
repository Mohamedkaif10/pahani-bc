from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date
import uuid

class PahaniRequest(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    district: str
    mandal: str
    village: str
    from_date: date
    to_date: date
    timestamp: Optional[int] = None
