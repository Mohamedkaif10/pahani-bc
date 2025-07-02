from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session, select
from app.db import get_session
from app.models.pahani import PahaniRequest
from app.models.user import User
from pydantic import BaseModel
from app.utils.auth_utils import get_current_user, require_admin
import os
import uuid
from app.utils.s3_utils import upload_pdf_to_s3
router = APIRouter()

UPLOAD_DIR = "uploads/pdfs" 
class ProcessRequest(BaseModel):
    id: str
    action: str 

@router.get("/admin/pahani-requests")
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
            "survey_number": r.survey_number,
            "from_year": r.from_year,
            "to_year": r.to_year,
            "timestamp": int(r.timestamp.timestamp() * 1000),
            "processed": r.processed,
            "user_id": r.user_id,
            "user_name": r.user.name if r.user else None
        }
        for r in results
    ]


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



@router.post("/admin/upload-pahani-pdf/{request_id}")
def upload_pahani_pdf(
    request_id: str,  
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin)
):
    pahani_request = session.exec(
        select(PahaniRequest).where(PahaniRequest.id == request_id)
    ).first()

    if not pahani_request:
        raise HTTPException(status_code=404, detail="Pahani request not found.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_data = file.file.read()
    s3_url = upload_pdf_to_s3(file_data, file.filename)

    pahani_request.pdf_s3_url = s3_url
    pahani_request.processed = True

    session.add(pahani_request)
    session.commit()

    return {
        "message": "PDF uploaded to S3 and request marked as processed",
        "s3_url": s3_url
    }

@router.post("/admin/approve-request/{request_id}")
def approve_request(
    request_id: str,
    session: Session = Depends(get_session),
    current_admin: User = Depends(require_admin)
):
    request = session.get(PahaniRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.processed = True
    session.add(request)
    session.commit()
    session.refresh(request)
    return {"message": "Request approved successfully", "data": request}