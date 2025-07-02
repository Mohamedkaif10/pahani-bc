from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
import uuid
from datetime import datetime, timezone

class PahaniRequest(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    district: str
    mandal: str
    village: str
    survey_number: str  
    from_year: int     
    to_year: int        
    area: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = Field(default=False)
    is_paid: bool = Field(default=False)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="requests")
    pdf_s3_url: Optional[str] = None
