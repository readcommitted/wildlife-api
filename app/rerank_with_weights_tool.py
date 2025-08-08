from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np

router = APIRouter()

# --- Models ---
class Candidate(BaseModel):
    common_name: str
    species: str
    eco_code: str
    image_similarity: float
    text_similarity: float
    color_similarity: Optional[float] = 0.0
    combined_score: float
    probability: float

class RerankRequest(BaseModel):
    top_candidates: List[Candidate]
    image_weight: float = Field(..., description="Weight for image similarity")
    text_weight: float = Field(..., description="Weight for text similarity")
    color_weight: float = Field(0.0, description="Weight for color similarity")

class RerankResponse(BaseModel):
    top_candidates: List[Candidate]
    best_match: Candidate
    rationale: Optional[str] = None

# --- Utility ---
def softmax(scores: List[float]) -> np.ndarray:
    exp_scores = np.exp(scores - np.max(scores))
    return exp_scores / exp_scores.sum()

# --- Endpoint ---
@router.post(
    "/species/rerank-with-weights",
    operation_id="rerank_with_weights",
    summary="Rerank species candidates with adjusted weights (image/text/color)",
    description="Recomputes combined scores and probabilities using updated image, text, and color similarity weights.",
    response_model=RerankResponse,
    tags=["Species"]
)
async def rerank_with_weights(request: RerankRequest) -> RerankResponse:
    recomputed = []
    for c in request.top_candidates:
        col_sim = c.color_similarity or 0.0
        combined = (
            request.image_weight * c.image_similarity +
            request.text_weight * c.text_similarity +
            request.color_weight * col_sim
        )
        recomputed.append((c, combined))

    scores = [r[1] for r in recomputed]
    probs = softmax(scores)

    candidates: List[Candidate] = []
    for i, (old, combined) in enumerate(recomputed):
        candidates.append(Candidate(
            common_name=old.common_name,
            species=old.species,
            eco_code=old.eco_code,
            image_similarity=old.image_similarity,
            text_similarity=old.text_similarity,
            color_similarity=old.color_similarity or 0.0,
            combined_score=combined,
            probability=float(probs[i])
        ))

    best_idx = int(np.argmax(probs))
    best = candidates[best_idx]

    rationale = (
        f"Reranked candidates using weights (image: {request.image_weight:.2f}, "
        f"text: {request.text_weight:.2f}, color: {request.color_weight:.2f}). "
        f"Best match is now {best.common_name} with probability {best.probability:.2f}."
    )

    return RerankResponse(
        top_candidates=candidates,
        best_match=best,
        rationale=rationale
    )
