# app/species_tools.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from db.db import SessionLocal
from fastapi import APIRouter
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

class SpeciesByRegion(BaseModel):
    ecoregion_code: str
    ecoregion_name: str
    class_name: str
    common_name: str
    conservation_status: str

@router.get(
    "/species/by-ecoregion",
    operation_id="get_species_by_ecoregion",
    summary="Get species found in a WWF ecoregion",
    description="Returns species observed in the specified WWF ecoregion.",
    response_model=List[SpeciesByRegion]
)
async def get_species_by_ecoregion(
    eco_code: str = Query(..., description="WWF ecoregion code (e.g., NA0528)")
) -> List[SpeciesByRegion]:
    session: Session = SessionLocal()
    try:
        rows = session.execute(
            """
            SELECT ecoregion_code, ecoregion_name, class_name, common_name, conservation_status
            FROM wildlife.species_by_region
            WHERE ecoregion_code = :eco_code
            """,
            {"eco_code": eco_code}
        ).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB query failed: {e}")
    if not rows:
        raise HTTPException(status_code=404, detail="No species found for this ecoregion")
    return [SpeciesByRegion(**dict(row)) for row in rows]
