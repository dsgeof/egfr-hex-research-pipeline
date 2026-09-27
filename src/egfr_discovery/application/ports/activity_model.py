from typing import Protocol

from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.prediction import ActivityPrediction


class ActivityModel(Protocol):

    def fit(self, compounds: list[Compound], labels: list[float]) -> None:
        ...

    def predict(self, compounds: list[Compound]) -> list[ActivityPrediction]:
        ...

    def save(self, destination: str) -> None:
        ...