from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np

router = APIRouter()

class Candidate(BaseModel):
    common_name: str
    species: str
    eco_code: str
    image_similarity: float
    text_similarity: float
    combined_score: float
    probability: float

class RerankRequest(BaseModel):
    top_candidates: List[Candidate]
    image_weight: float = Field(..., description="New weight for image similarity")
    text_weight: float = Field(..., description="New weight for text similarity")

class RerankResponse(BaseModel):
    top_candidates: List[Candidate]
    best_match: Candidate
    rationale: Optional[str] = None

def softmax(scores):
    exp_scores = np.exp(scores - np.max(scores))
    return exp_scores / exp_scores.sum()

@router.post(
    "/species/rerank-with-weights",
    operation_id="rerank_with_weights",
    summary="Rerank species candidates with adjusted weights",
    description="Recomputes combined scores and probabilities using updated image/text similarity weights.",
    response_model=RerankResponse,
    tags=["Species"]
)
async def rerank_with_weights(request: RerankRequest) -> RerankResponse:
    # --- Step 1: Recompute combined scores ---
    recomputed = []
    for c in request.top_candidates:
        combined = request.image_weight * c.image_similarity + request.text_weight * c.text_similarity
        recomputed.append((c, combined))

    # --- Step 2: Compute softmax ---
    scores = [r[1] for r in recomputed]
    probs = softmax(scores)

    # --- Step 3: Build new candidate list ---
    candidates: List[Candidate] = []
    for i, (old, combined) in enumerate(recomputed):
        candidates.append(Candidate(
            common_name=old.common_name,
            species=old.species,
            eco_code=old.eco_code,
            image_similarity=old.image_similarity,
            text_similarity=old.text_similarity,
            combined_score=combined,
            probability=float(probs[i])
        ))

    best_idx = int(np.argmax(probs))
    best = candidates[best_idx]

    rationale = (
        f"Reranked candidates using weights (image: {request.image_weight:.1f}, text: {request.text_weight:.1f}). "
        f"Best match is now {best.common_name} with probability {best.probability:.2f}."
    )

    return RerankResponse(
        top_candidates=candidates,
        best_match=best,
        rationale=rationale
    )
