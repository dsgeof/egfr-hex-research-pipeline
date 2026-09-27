from dataclasses import dataclass

from egfr_discovery.domain.compound import Compound
"""Module defining the ActivityPrediction dataclass for EGFR discovery."""

# Dataclass representing a bioactivity prediction for a compound.
@dataclass(frozen=True, slots=True)
class ActivityPrediction:
    # The compound for which the activity prediction is made.
    compound: Compound
    # The predicted probability of the compound being active.
    predicted_probability: float
    # The uncertainty associated with the predicted probability.
    uncertainty: float | None = None

    # Post-initialization method to validate the predicted probability and uncertainty.
    def __post_init__(self) -> None:
        # Validate the predicted probability and uncertainty values.
        if not 0.0 <= self.predicted_probability <= 1.0:
            raise ValueError("predicted_probability must be between 0 and 1")

        if self.uncertainty is not None and self.uncertainty < 0.0:
            raise ValueError("uncertainty cannot be negative")