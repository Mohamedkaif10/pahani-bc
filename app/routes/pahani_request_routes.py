from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app.models.pahani import PahaniRequest
from app.utils.auth_utils import get_current_user,require_admin
router = APIRouter()
from app.models.user import User
from fastapi.responses import FileResponse

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


