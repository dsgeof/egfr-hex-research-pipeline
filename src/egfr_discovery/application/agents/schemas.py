from typing import Literal

from pydantic import BaseModel, Field


class CandidateConcern(BaseModel):
    category: Literal[
        "uncertainty",
        "training_similarity",
        "structural_alert",
        "missing_data",
    ]
    explanation: str


class CandidateReview(BaseModel):
    compound_id: str
    recommendation: Literal[
        "prioritize",
        "hold",
        "reject",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    concerns: list[CandidateConcern]
    rationale: str