
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.auth_utils import get_current_user
from app.models.user import User
import stripe
from app.utils.stripe_utils import stripe  

router = APIRouter()

class PaymentRequest(BaseModel):
    amount: int 

@router.post("/create-payment-intent")
def create_payment_intent(
    payment: PaymentRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        intent = stripe.PaymentIntent.create(
            amount=payment.amount * 100,  
            currency="inr",
            metadata={"user_id": current_user.id}
        )
        return {"clientSecret": intent["client_secret"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
