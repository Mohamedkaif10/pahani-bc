from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
import uuid

class PaymentTransaction(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    request_id: str = Field(foreign_key="pahanirequest.id")
    user_id: int = Field(foreign_key="user.id")
    transaction_id: str = Field(unique=True, index=True)
    amount: float
    status: str = Field(default="pending")  # pending, verified, failed
    payment_method: str = Field(default="upi")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = Field(default=None, foreign_key="user.id")
    
    request: Optional["PahaniRequest"] = Relationship()
    user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PaymentTransaction.user_id]"}
    )
    verified_by_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[PaymentTransaction.verified_by]"}
    )