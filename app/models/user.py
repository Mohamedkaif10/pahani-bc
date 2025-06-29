from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str
    role: str  

    email: Optional[str] = Field(default=None, index=True, unique=True)
    password: Optional[str] = None
    aadhaar_number: Optional[str] = Field(default=None, index=True, unique=True)
    patadar_passbook_number: Optional[str] = None
    phone_number: Optional[str] = None
    
    requests: List["PahaniRequest"] = Relationship(back_populates="user")
