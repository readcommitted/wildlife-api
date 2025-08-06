from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from db.db import SessionLocal

router = APIRouter()


class EcoregionResponse(BaseModel):
    eco_code: str


@router.get(
    "/ecoregion/by-coordinates",
    operation_id="get_ecoregion_by_coordinates",
    summary="Get WWF ecoregion by coordinates",
    description="Returns the WWF ecoregion code for the given lat/lon point.",
    response_model=EcoregionResponse,
    tags=["Ecoregion"]
)
async def get_ecoregion_by_coordinates(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
) -> EcoregionResponse:
    """Returns eco_code for given lat/lon (spatial lookup in DB)."""
    try:
        with SessionLocal() as session:
            result = session.execute(
                text("SELECT eco_code FROM public.get_ecoregion_by_coords(:lat, :lon) LIMIT 1"),
                {"lat": lat, "lon": lon}
            ).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Ecoregion not found for these coordinates")

        return EcoregionResponse(eco_code=result["eco_code"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")
