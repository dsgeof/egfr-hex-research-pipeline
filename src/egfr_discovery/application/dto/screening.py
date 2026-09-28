from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from egfr_discovery.application.dto.model_results import ModelValidationResult
from egfr_discovery.domain.candidate import CandidateProperties
from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.prediction import ActivityPrediction


@dataclass(frozen=True, slots=True)
class ScreeningLibrary:
    library_id: str
    compounds: tuple[Compound, ...]
    source_path: str


@dataclass(frozen=True, slots=True)
class EvaluatedCandidate:
    prediction: ActivityPrediction
    properties: CandidateProperties


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    rank: int
    compound_id: str
    smiles: str
    predicted_pic50: float
    uncertainty: float | None
    properties: CandidateProperties
    score: float
    source_library_id: str


class ScreeningPipelineCommand(BaseModel):
    library_path: Path
    target_id: str = Field(default="CHEMBL203", min_length=1)
    activity_type: str = Field(default="IC50", min_length=1)
    validation_fraction: float = Field(default=0.2, gt=0.0, lt=1.0)
    random_seed: int = 42
    max_validation_mae: float = Field(default=1.0, gt=0.0)
    shortlist_size: int = Field(default=100, gt=0)
    similarity_threshold: float = Field(default=0.7, gt=0.0, le=1.0)
    top_n: int = Field(default=20, gt=0)
    output_path: Path = Path("artifacts/screening/ranked_candidates.csv")


@dataclass(frozen=True, slots=True)
class ScreeningPipelineResult:
    fetched_count: int
    curated_count: int
    rejected_count: int
    screened_count: int
    filtered_count: int
    diverse_count: int
    validation: ModelValidationResult
    ranked_candidates: tuple[RankedCandidate, ...]
    artifact_paths: tuple[str, ...]
    disclaimer: str
