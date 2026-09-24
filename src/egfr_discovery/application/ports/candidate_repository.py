from typing import Protocol

from egfr_discovery.domain.prediction import ActivityPrediction


class CandidateRepository(Protocol):
    def get(self, compound_id: str) -> ActivityPrediction | None:
        """Retrieve one candidate prediction."""