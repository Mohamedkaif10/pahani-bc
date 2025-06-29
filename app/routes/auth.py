from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from app.models.user import User
from app.db import get_session
from typing import Optional
from app.utils.auth_utils import create_token
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta
from twilio.rest import Client
import os
from app.utils.auth_utils import create_access_token
load_dotenv()
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    name: str
    aadhaar_number: str
    patadar_passbook_number: str
    phone_number: str  # <- add this field

class LoginData(BaseModel):
    email: EmailStr
    password: str

class SendOTPRequest(BaseModel):
    phone_number: str

class VerifyOTPRequest(BaseModel):
    phone_number: str
    otp: str

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_VERIFY_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")
JWT_SECRET = os.getenv("JWT_SECRET")

twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

@router.post("/register/admin")
def register_admin(data: AdminCreate, db: Session = Depends(get_session)):
    existing = db.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(data.password)
    user = User(
        name=data.name,
        email=data.email,
        password=hashed_password,
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Admin registered", "user": user}


@router.post("/register/user")
def register_user(data: UserCreate, db: Session = Depends(get_session)):
    existing = db.exec(
        select(User).where(
            (User.aadhaar_number == data.aadhaar_number) &
            (User.patadar_passbook_number == data.patadar_passbook_number)
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already registered")

    user = User(
        name=data.name,
        aadhaar_number=data.aadhaar_number,
        patadar_passbook_number=data.patadar_passbook_number,
        phone_number=data.phone_number,
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered", "user": user}

@router.post("/send-otp")
def send_otp(data: SendOTPRequest):
    phone = data.phone_number
    if not phone.isdigit() or len(phone) != 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    try:
        twilio_client.verify.v2.services(TWILIO_VERIFY_SID).verifications.create(
            to=f"+91{phone}", channel="sms"
        )
        return {"message": "OTP sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login/user")
def verify_otp(
    data: VerifyOTPRequest,
    session: Session = Depends(get_session)
):
    try:
        phone = data.phone_number
        otp = data.otp

        # 1. Verify OTP
        verification = twilio_client.verify.v2.services(
            os.getenv("TWILIO_VERIFY_SERVICE_SID")
        ).verification_checks.create(to=f'+91{phone}', code=otp)

        if verification.status != "approved":
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # 2. Check user existence
        user = session.exec(select(User).where(User.phone_number == phone)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 3. Return token
        token = create_access_token({"sub": str(user.id)})
        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "role": user.role,
                "phone_number": user.phone_number,
            }
        }

    except Exception as e:
        print("❌ OTP Login Error:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

def login(data: LoginData, db: Session, role: str):
    user = db.exec(select(User).where(User.email == data.email)).first()

    if not user or not pwd_context.verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role != role:
        raise HTTPException(status_code=403, detail=f"{role.capitalize()} access required")

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }
    }

@router.post("/login/admin")
def login_admin(data: LoginData, db: Session = Depends(get_session)):
    return login(data, db, role="admin")

