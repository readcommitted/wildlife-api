# app/main.py
from fastapi import FastAPI, APIRouter, Query, HTTPException
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


load_dotenv()

# MCP template uses routers, but you can keep it simple for now
app = FastAPI(title="Wildlife MCP API Quickstart")
router = APIRouter()

def get_db_conn():
    # Read DATABASE_URL from environment (DO App Platform or local .env)
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL env variable not set!")
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    return conn

@router.get("/ecoregion/by-coordinates")
def get_ecoregion_by_coordinates(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """Returns eco_code for given lat/lon (spatial lookup in DB)."""
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT eco_code FROM public.get_ecoregion_by_coords(%s, %s) LIMIT 1",
                (lat, lon)
            )
            result = cur.fetchone()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")
    if not result:
        raise HTTPException(status_code=404, detail="Ecoregion not found for these coordinates")
    return {"eco_code": result["eco_code"]}

# Add the router to app
app.include_router(router)
