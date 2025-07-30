# app/species_tools.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from db.db import SessionLocal
from fastapi import APIRouter
from dotenv import load_dotenv
from sqlalchemy import text
from typing import Optional

load_dotenv()

router = APIRouter()

class SpeciesByRegion(BaseModel):
    ecoregion_code: str
    ecoregion_name: str
    class_name: str
    common_name: str
    conservation_status: Optional[str]

@router.get(
    "/species/by-ecoregion",
    operation_id="get_species_by_ecoregion",
    summary="Get species found in a WWF ecoregion",
    description="Returns species observed in the specified WWF ecoregion.",
    response_model=List[SpeciesByRegion],
    tags=["Species"]
)
async def get_species_by_ecoregion(
    eco_code: str = Query(..., description="WWF ecoregion code (e.g., NA0528)")
) -> List[SpeciesByRegion]:
    session: Session = SessionLocal()
    try:

        rows = session.execute(text("""
            SELECT ecoregion_code, ecoregion_name, class_name, common_name, conservation_status
            FROM wildlife.species_by_region
            WHERE common_name is not null and ecoregion_code = :eco_code
        """), {"eco_code": eco_code})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB query failed: {e}")
    if not rows:
        raise HTTPException(status_code=404, detail="No species found for this ecoregion")
    return [SpeciesByRegion(**row._mapping) for row in rows]

