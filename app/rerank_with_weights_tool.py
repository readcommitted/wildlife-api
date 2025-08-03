from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
import numpy as np
from db.db import SessionLocal
from db.species_model import SpeciesEmbedding
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

class RerankRequest(BaseModel):
    image_id: int = Field(..., description="Image ID (for logging/debugging)")
    embedding: List[float] = Field(..., description="OpenCLIP 1024-dim image embedding")
    top_candidates: List[str] = Field(..., description="List of species identifiers to rerank")
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

class RerankResponse(BaseModel):
    top_candidates: List[Candidate]
    best_match: Candidate
    rationale: Optional[str] = None

def cosine_similarity(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

@router.post(
    "/species/rerank-with-weights",
    operation_id="rerank_with_weights",
    summary="Rerank existing species candidates with new weights",
    description="Takes a list of candidate species and reranks using image-text similarity with provided weights.",
    response_model=RerankResponse,
    tags=["Species"]
)
async def rerank_with_weights(request: RerankRequest) -> RerankResponse:
    session: Session = SessionLocal()
    embedding_np = np.array(request.embedding, dtype=np.float32)

    scored_candidates = []
    for species_id in request.top_candidates:
        db_row = session.query(SpeciesEmbedding).filter_by(species=species_id).first()
        if not db_row or db_row.image_embedding is None or db_row.text_embedding is None:
            continue
        img_sim = cosine_similarity(embedding_np, db_row.image_embedding)
        text_sim = cosine_similarity(embedding_np, db_row.text_embedding)
        combined = request.image_weight * img_sim + request.text_weight * text_sim
        scored_candidates.append((
            db_row.common_name,
            db_row.species,
            db_row.ecoregion_code or "",
            img_sim,
            text_sim,
            combined
        ))

    if not scored_candidates:
        raise HTTPException(status_code=404, detail="No valid candidates with embeddings found")

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

    best_idx = int(np.argmax(probs))
    best = candidates[best_idx]

    rationale = (
        f"Reranked using weights (image: {request.image_weight:.1f}, text: {request.text_weight:.1f}). "
        f"New best match: {best.common_name} with probability {best.probability:.2f}."
    )

    return RerankResponse(
        top_candidates=candidates,
        best_match=best,
        rationale=rationale
    )
