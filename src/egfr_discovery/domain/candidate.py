from dataclasses import dataclass

from egfr_discovery.domain.compound import Compound


@dataclass(frozen=True, slots=True)
class CandidateProperties:
    molecular_weight: float
    log_p: float
    hydrogen_bond_donors: int
    hydrogen_bond_acceptors: int
    polar_surface_area: float


@dataclass(frozen=True, slots=True)
class Candidate:
    compound: Compound
    predicted_pic50: float
    properties: CandidateProperties
    diversity_score: float | None = None
    rank_score: float | None = None