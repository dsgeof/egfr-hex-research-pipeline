from typing import Protocol

from egfr_discovery.domain.prediction import ActivityPrediction

# Protocol defining the interface for a candidate repository (CRUD operations for candidate predictions)
class CandidateRepository(Protocol):
    def get(self, compound_id: str) -> ActivityPrediction | None:
        """Retrieve one candidate prediction by its compound ID. Returns None if not found."""