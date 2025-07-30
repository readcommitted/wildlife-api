# app/species_tools.py

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from collections import defaultdict
from typing import Optional, List, Dict
from sqlalchemy import text
from db.db import SessionLocal
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# --- Response Models ---

class SpeciesItem(BaseModel):
    common_name: str
    conservation_status: Optional[str]

class GroupedSpeciesResponse(BaseModel):
    ecoregion_code: str
    ecoregion_name: str
    species_by_class: Dict[str, List[SpeciesItem]]


# --- Endpoint ---

@router.get(
    "/species/by-ecoregion",
    operation_id="get_species_by_ecoregion",
    summary="Get species found in a WWF ecoregion",
    description="Returns species observed in the specified WWF ecoregion.",
    response_model=GroupedSpeciesResponse,
    tags=["Species"]
)
async def get_species_by_ecoregion(
    eco_code: str = Query(..., description="WWF ecoregion code (e.g., NA0528)")
) -> GroupedSpeciesResponse:
    session: Session = SessionLocal()
    try:
        rows = session.execute(text("""
            SELECT ecoregion_code, ecoregion_name, class_name, common_name, conservation_status
            FROM wildlife.species_by_region
            WHERE common_name IS NOT NULL AND ecoregion_code = :eco_code
        """), {"eco_code": eco_code}).fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB query failed: {e}")

    if not rows:
        raise HTTPException(status_code=404, detail="No species found for this ecoregion")

    # Static values (same across all rows)
    first = rows[0]._mapping
    ecoregion_code = first["ecoregion_code"]
    ecoregion_name = first["ecoregion_name"]

    # Group species by class
    species_by_class = defaultdict(list)
    for row in rows:
        m = row._mapping
        species_by_class[m["class_name"]].append({
            "common_name": m["common_name"],
            "conservation_status": m["conservation_status"]
        })

    return {
        "ecoregion_code": ecoregion_code,
        "ecoregion_name": ecoregion_name,
        "species_by_class": species_by_class
    }

