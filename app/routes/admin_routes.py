from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.pahani import PahaniRequest
from pydantic import BaseModel

router = APIRouter()


@router.get("/admin/pahani-requests")
def get_all_requests(session: Session = Depends(get_session)):
    return session.exec(select(PahaniRequest)).all()


class ProcessRequest(BaseModel):
    id: str
    action: str 


@router.post("/admin/pahani-requests/process")
def mark_processed(req: ProcessRequest, session: Session = Depends(get_session)):
    request = session.get(PahaniRequest, req.id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if req.action == "process":
        request.processed = True
        session.add(request)
        session.commit()
        session.refresh(request)
        return {"message": "Marked as processed", "data": request}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
