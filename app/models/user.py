from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    password: str
    role: str  # 'admin' or 'user'

    requests: List["PahaniRequest"] = Relationship(back_populates="user")
