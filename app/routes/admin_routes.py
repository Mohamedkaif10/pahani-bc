from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.pahani import PahaniRequest
from pydantic import BaseModel

router = APIRouter()

UPLOAD_DIR = "uploads/pdfs" 

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



@router.post("/admin/upload-pahani-pdf/{request_id}")
def upload_pahani_pdf(
    request_id: int,
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
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    pahani_request.pdf_file_path = file_path
    session.add(pahani_request)
    session.commit()

    return {"message": "PDF uploaded successfully", "file_path": file_path}