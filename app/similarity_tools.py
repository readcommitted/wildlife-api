from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np
from db.db import SessionLocal
from db.species_model import SpeciesEmbedding
from sqlalchemy import text
from tools.color_utils import (
    get_image_colors,
    get_species_color_profile,
    compute_color_similarity,
    get_color_vocab
)

router = APIRouter()

# --- Request/Response Models ---
class IdentificationRequest(BaseModel):
    image_id: int = Field(..., description="Image ID (for logging/debugging)")
    embedding: List[float] = Field(..., description="OpenCLIP 1024-dim image embedding")
    lat: float = Field(..., description="Latitude of the image location")
    lon: float = Field(..., description="Longitude of the image location")
    top_n: int = Field(5, description="Number of candidate species to return")
    image_weight: float = Field(0.6, description="Weight for image similarity")
    text_weight: float = Field(0.4, description="Weight for text similarity")
    color_weight: float = Field(0.0, description="Weight for color similarity")

class Candidate(BaseModel):
    common_name: str
    species: str
    eco_code: str
    image_similarity: float
    text_similarity: float
    color_similarity: Optional[float] = None
    image_colors: Optional[dict] = None
    species_colors: Optional[dict] = None
    combined_score: float
    probability: float


class IdentificationResponse(BaseModel):
    top_candidates: List[Candidate]
    best_match: Candidate
    rationale: Optional[str] = None


# --- Utility ---
def cosine_similarity(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# --- Endpoint ---
@router.post(
    "/species/identify-by-embedding",
    operation_id="identify_species_by_embedding",
    summary="Identify species based on image embedding and location",
    description="Returns top-N species using image-text-color similarity, with final match chosen using weights or LLM reasoning.",
    response_model=IdentificationResponse,
    tags=["Species"]
)
async def identify_species(request: IdentificationRequest) -> IdentificationResponse:
    try:
        with SessionLocal() as session:
            sql = text("""
                SELECT species, common_name, image_path, distance, eco_code
                FROM wildlife.usf_rank_species_candidates(
                    (:lat)::double precision,
                    (:lon)::double precision,
                    (:embedding)::vector,
                    :top_n
                )
            """)

            top_candidates = session.execute(sql, {
                "lat": request.lat,
                "lon": request.lon,
                "embedding": np.array(request.embedding, dtype=np.float32).tolist(),
                "top_n": request.top_n
            }).fetchall()

            if not top_candidates:
                raise HTTPException(status_code=404, detail="No candidates found")

            image_colors = get_image_colors(session, request.image_id)
            vocab = get_color_vocab(session)

            scored_candidates = []
            for row in top_candidates:
                species, common_name, _, distance, eco_code = row
                db_row = session.query(SpeciesEmbedding).filter_by(species=species).first()
                if not db_row or db_row.text_embedding is None:
                    continue

                img_sim = 1 - distance
                text_sim = cosine_similarity(request.embedding, db_row.text_embedding)
                species_colors = get_species_color_profile(session, common_name)
                color_sim = compute_color_similarity(image_colors, species_colors, vocab)

                combined = (
                    request.image_weight * img_sim +
                    request.text_weight * text_sim +
                    request.color_weight * color_sim
                )

                scored_candidates.append((
                    common_name, species, eco_code, img_sim, text_sim, color_sim, combined, image_colors, species_colors
                ))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB operation failed: {e}")

    if not scored_candidates:
        raise HTTPException(status_code=404, detail="No candidates with valid text embeddings")

    scores = [x[6] for x in scored_candidates]
    exp_scores = np.exp(scores)
    probs = exp_scores / np.sum(exp_scores)

    candidates: List[Candidate] = []
    for i, (common_name, species, eco_code, img_sim, text_sim, color_sim, combined, img_cols, sp_cols) in enumerate(scored_candidates):
        candidates.append(Candidate(
            common_name=common_name,
            species=species,
            eco_code=eco_code,
            image_similarity=img_sim,
            text_similarity=text_sim,
            color_similarity=color_sim,
            image_colors=img_cols,
            species_colors=sp_cols,
            combined_score=combined,
            probability=float(probs[i])
        ))

    best_idx = int(np.argmax(probs))
    best = candidates[best_idx]

    rationale = (
        f"Selected best match using weights (image: {request.image_weight:.1f}, "
        f"text: {request.text_weight:.1f}, color: {request.color_weight:.1f}). "
        f"Best candidate: {best.common_name} with probability {best.probability:.2f}."
    )

    return IdentificationResponse(
        top_candidates=candidates,
        best_match=best,
        rationale=rationale
    )
