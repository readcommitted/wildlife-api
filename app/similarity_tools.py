from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
import numpy as np
from db.db import SessionLocal
from db.species_model import SpeciesEmbedding
from dotenv import load_dotenv
from fastapi import APIRouter
from sqlalchemy import text

load_dotenv()

router = APIRouter()

class IdentificationRequest(BaseModel):
    image_id: int = Field(..., description="Image ID (for logging/debugging)")
    embedding: List[float] = Field(..., description="OpenCLIP 1024-dim image embedding")
    lat: float = Field(..., description="Latitude of the image location")
    lon: float = Field(..., description="Longitude of the image location")
    top_n: int = Field(5, description="Number of candidate species to return")
    image_weight: float = Field(0.6, description="Weight for image similarity")
    text_weight: float = Field(0.4, description="Weight for text similarity")


class Candidate(BaseModel):
    common_name: str
    species: str
    eco_code: str
    image_similarity: float
    text_similarity: float
    combined_score: float
    probability: float


class IdentificationResponse(BaseModel):
    top_candidates: List[Candidate]
    best_match: Candidate
    rationale: Optional[str] = None


def cosine_similarity(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@router.post(
    "/species/identify-by-embedding",
    operation_id="identify_species_by_embedding",
    summary="Identify species based on image embedding and location",
    description="Returns top-N species using image-text similarity, with final match chosen using weights or LLM reasoning.",
    response_model=IdentificationResponse,
    tags=["Species"]
)
async def identify_species(request: IdentificationRequest) -> IdentificationResponse:
    session: Session = SessionLocal()

    # --- Step 1: Candidate lookup from DB ---
    sql = text("""
        SELECT species, common_name, image_path, distance, eco_code
        FROM wildlife.usf_rank_species_candidates(
            (:lat)::double precision,
            (:lon)::double precision,
            (:embedding)::vector,
            :top_n
        )
    """)

    try:
        top_candidates = session.execute(sql, {
            "lat": request.lat,
            "lon": request.lon,
            "embedding": np.array(request.embedding, dtype=np.float32).tolist(),
            "top_n": request.top_n
        }).fetchall()
        session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB candidate selection failed: {e}")

    if not top_candidates:
        raise HTTPException(status_code=404, detail="No candidates found")

    # --- Step 2: Score with text embeddings ---
    scored_candidates = []
    for row in top_candidates:
        species, common_name, _, distance, eco_code = row
        db_row = session.query(SpeciesEmbedding).filter_by(species=species).first()
        if not db_row or db_row.text_embedding is None:
            continue
        img_sim = 1 - distance
        text_sim = cosine_similarity(request.embedding, db_row.text_embedding)
        combined = request.image_weight * img_sim + request.text_weight * text_sim
        scored_candidates.append((common_name, species, eco_code, img_sim, text_sim, combined))

    if not scored_candidates:
        raise HTTPException(status_code=404, detail="No candidates with valid text embeddings")

    # --- Step 3: Softmax probability ---
    scores = [x[5] for x in scored_candidates]
    exp_scores = np.exp(scores)
    probs = exp_scores / np.sum(exp_scores)

    candidates: List[Candidate] = []
    for i, (common_name, species, eco_code, img_sim, text_sim, combined) in enumerate(scored_candidates):
        candidates.append(Candidate(
            common_name=common_name,
            species=species,
            eco_code=eco_code,
            image_similarity=img_sim,
            text_similarity=text_sim,
            combined_score=combined,
            probability=float(probs[i])
        ))

    # --- Step 4: Best match ---
    best_idx = int(np.argmax(probs))
    best = candidates[best_idx]

    # --- Step 5: Placeholder LLM rationale ---
    rationale = (
        f"Selected best match using weights (image: {request.image_weight:.1f}, text: {request.text_weight:.1f}). "
        f"Best candidate: {best.common_name} with probability {best.probability:.2f}."
    )

    return IdentificationResponse(
        top_candidates=candidates,
        best_match=best,
        rationale=rationale
    )
