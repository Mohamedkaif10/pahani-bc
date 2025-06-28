from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.pahani import PahaniRequest
from app.utils.auth_utils import get_current_user,require_admin
router = APIRouter()
from app.models.user import User
from fastapi.responses import FileResponse
import razorpay
from fastapi import Request
from dotenv import load_dotenv
import os

load_dotenv()

RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

@router.post("/pahani-request")
def create_request(
    request: PahaniRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    request.user_id = current_user.id
    session.add(request)
    session.commit()
    session.refresh(request)
    return {"message": "Pahani request saved", "data": request}


@router.get("/pahani-request")
def get_all_requests(session: Session = Depends(get_session)):
    return session.exec(select(PahaniRequest)).all()


@router.get("/pahani-request/{request_id}")
def get_request_by_id(request_id: str, session: Session = Depends(get_session)):
    req = session.get(PahaniRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req
    
@router.get("/user/my-pahani-requests")
def get_user_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    requests = session.exec(
        select(PahaniRequest).where(PahaniRequest.user_id == current_user.id)
    ).all()
    return requests

@router.get("admin/pahani-request")
def get_all_requests(
    session: Session = Depends(get_session),
    current_admin: User = Depends(require_admin)
):
    results = session.exec(select(PahaniRequest)).all()

    return [
        {
            "id": r.id,
            "district": r.district,
            "mandal": r.mandal,
            "village": r.village,
            "from_date": r.from_date,
            "to_date": r.to_date,
            "processed": r.processed,
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else None
        }
        for r in results
    ]

@router.get("admin/pahani-request/{request_id}")
def get_request_by_id(
    request_id: str,
    session: Session = Depends(get_session),
    current_admin: User = Depends(require_admin)
):
    req = session.get(PahaniRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        "id": req.id,
        "district": req.district,
        "mandal": req.mandal,
        "village": req.village,
        "from_date": req.from_date,
        "to_date": req.to_date,
        "processed": req.processed,
        "user_id": req.user_id,
        "user_name": req.user.name if req.user else None
    }    

@router.get("/user/pahani-request-status/{request_id}")
def get_pahani_request_status(
    request_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    request = session.exec(
        select(PahaniRequest).where(
            (PahaniRequest.id == request_id) &
            (PahaniRequest.user_id == current_user.id)
        )
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    return {
        "pdf_ready": bool(request.pdf_s3_url),
        "is_paid": request.is_paid,
        "pdf_link": request.pdf_s3_url if request.is_paid else None,
        "message": (
            "PDF ready. Please complete payment to view." if request.pdf_s3_url and not request.is_paid
            else "PDF available." if request.is_paid
            else "PDF not yet uploaded."
        )
    }
@router.post("/user/create-payment/{request_id}")
def create_payment_order(
    request_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    req = session.get(PahaniRequest, request_id)
    if not req or req.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.is_paid:
        raise HTTPException(status_code=400, detail="Already paid")

    amount = 49900  # ₹499.00 in paisa

    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "receipt": f"receipt_{request_id}",
        "payment_capture": 1
    })

    return {
        "order_id": razorpay_order["id"],
        "razorpay_key": RAZORPAY_KEY,
        "amount": amount,
        "currency": "INR"
    }


@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request, session: Session = Depends(get_session)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")

    try:
        razorpay_client.utility.verify_webhook_signature(
            body, signature, os.getenv("RAZORPAY_WEBHOOK_SECRET")
        )
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    if payload.get("event") == "payment.captured":
        razorpay_order_id = payload["payload"]["payment"]["entity"]["order_id"]
        receipt_id = payload["payload"]["payment"]["entity"]["receipt"]

        request_id = receipt_id.replace("receipt_", "")

        req = session.get(PahaniRequest, request_id)
        if req:
            req.is_paid = True
            session.add(req)
            session.commit()

    return {"status": "ok"}
        
@router.get("/user/view-pahani-pdf/{request_id}")
def view_uploaded_pdf(
    request_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    pahani_request = session.exec(
        select(PahaniRequest).where(
            (PahaniRequest.id == request_id) &
            (PahaniRequest.user_id == current_user.id)
        )
    ).first()

    if not pahani_request:
        raise HTTPException(status_code=404, detail="Request not found")

    if not pahani_request.is_paid:
        raise HTTPException(status_code=403, detail="Please complete payment to access the document.")

    if not pahani_request.pdf_file_path:
        raise HTTPException(status_code=404, detail="PDF not uploaded yet.")

    return FileResponse(path=pahani_request.pdf_file_path, media_type="application/pdf", filename="pahani.pdf")


