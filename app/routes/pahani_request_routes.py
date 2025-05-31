from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.pahani import PahaniRequest

router = APIRouter()


@router.post("/pahani-request")
def create_request(request: PahaniRequest, session: Session = Depends(get_session)):
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
