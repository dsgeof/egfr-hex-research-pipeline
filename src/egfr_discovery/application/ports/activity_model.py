from typing import Protocol, Sequence

from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.prediction import ActivityPrediction

# Port
# Protocol defining the interface for an activity prediction ml model.
# This protocol can be implemented by any machine learning model that predicts activity for compounds.
# CSV → training service → model artifact → predictions
class ActivityModel(Protocol):
    def train(
        self,
        compounds: Sequence[Compound],
        labels: Sequence[int],
    ) -> None:
        """Train the activity model."""

    def predict(
        self,
        compounds: Sequence[Compound],
    ) -> list[ActivityPrediction]:
        """Predict activity for compounds."""

    def save(self, destination: str) -> None:
        """Persist the trained model."""