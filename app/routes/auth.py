from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from app.models.user import User
from app.db import get_session

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    aadhaar_number: Optional[str] = None
    patadar_passbook_number: Optional[str] = None
    survey_number: Optional[str] = None

class LoginData(BaseModel):
    email: EmailStr
    password: str


def register_user(data: UserCreate, db: Session, role: str):
    existing = db.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(data.password)
    user = User(name=data.name, email=data.email, password=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": f"{role.capitalize()} registered successfully", "id": user.id}


@router.post("/register/admin")
def register_admin(data: UserCreate, db: Session = Depends(get_session)):
    return register_user(data, db, role="admin")

@router.post("/register/user")
def register_user_route(data: UserCreate, db: Session = Depends(get_session)):
    return register_user(data, db, role="user")


def login(data: LoginData, db: Session, role: str):
    user = db.exec(select(User).where(User.email == data.email, User.role == role)).first()
    if not user or not pwd_context.verify(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.id)
    return {
        "message": f"{role.capitalize()} logged in successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role}
    }


@router.post("/login/admin")
def login_admin(data: LoginData, db: Session = Depends(get_session)):
    return login(data, db, role="admin")

@router.post("/login/user")
def login_user(data: LoginData, db: Session = Depends(get_session)):
    return login(data, db, role="user")
