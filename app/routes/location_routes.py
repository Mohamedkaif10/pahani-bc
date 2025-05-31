from fastapi import APIRouter, HTTPException
from app.utils.location_data import load_location_data

router = APIRouter()
location_data = load_location_data() 

@router.get("/districts")
def get_districts():
    return list(location_data.keys())

@router.get("/mandals/{district}")
def get_mandals(district: str):
    if district not in location_data:
        raise HTTPException(status_code=404, detail="District not found")
    return list(location_data[district].keys())

@router.get("/villages/{district}/{mandal}")
def get_villages(district: str, mandal: str):
    if district not in location_data or mandal not in location_data[district]:
        raise HTTPException(status_code=404, detail="Mandal not found")
    return location_data[district][mandal]
