from dataclasses import dataclass
from math import isfinite

from egfr_discovery.domain.compound import Compound


@dataclass(frozen=True, slots=True)
class ActivityPrediction:
    compound: Compound
    predicted_pic50: float
    uncertainty: float | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.predicted_pic50):
            raise ValueError("predicted_pic50 must be finite")
        if self.uncertainty is not None and (
            not isfinite(self.uncertainty) or self.uncertainty < 0
        ):
            raise ValueError("uncertainty must be finite and non-negative")
