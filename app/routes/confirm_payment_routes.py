from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from app.db import get_session
from app.models.pahani import PahaniRequest
from app.models.payment import PaymentTransaction
from app.models.user import User
from app.utils.auth_utils import get_current_user
from datetime import datetime, timezone

router = APIRouter()

class PaymentConfirmRequest(BaseModel):
    request_id: str
    transaction_id: str

@router.post("/user/confirm-payment")
def confirm_payment(
    payment_data: PaymentConfirmRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    pahani_request = session.exec(
        select(PahaniRequest).where(
            (PahaniRequest.id == payment_data.request_id) &
            (PahaniRequest.user_id == current_user.id)
        )
    ).first()
    
    if not pahani_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if not pahani_request.processed:
        raise HTTPException(status_code=400, detail="Request not yet processed")
    
    if pahani_request.is_paid:
        raise HTTPException(status_code=400, detail="Payment already completed")
    
    existing_payment = session.exec(
        select(PaymentTransaction).where(
            PaymentTransaction.transaction_id == payment_data.transaction_id
        )
    ).first()
    
    if existing_payment:
        raise HTTPException(status_code=400, detail="Transaction ID already used")
    
    year_difference = pahani_request.to_year - pahani_request.from_year + 1
    amount = year_difference * 10.0
    
    payment_transaction = PaymentTransaction(
        request_id=payment_data.request_id,
        user_id=current_user.id,
        transaction_id=payment_data.transaction_id,
        amount=amount,
        status="pending"
    )
    
    session.add(payment_transaction)
    session.commit()
    session.refresh(payment_transaction)
    
    return {
        "message": "Payment confirmation submitted. Please wait for admin verification.",
        "payment_id": payment_transaction.id,
        "amount": amount,
        "status": "pending"
    }

@router.get("/user/payment-status/{request_id}")
def get_payment_status(
    request_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    payment = session.exec(
        select(PaymentTransaction).where(
            (PaymentTransaction.request_id == request_id) &
            (PaymentTransaction.user_id == current_user.id)
        )
    ).first()
    
    if not payment:
        return {"status": "no_payment", "message": "No payment found for this request"}
    
    return {
        "status": payment.status,
        "transaction_id": payment.transaction_id,
        "amount": payment.amount,
        "created_at": payment.created_at,
        "verified_at": payment.verified_at
    }