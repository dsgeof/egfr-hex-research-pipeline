from egfr_discovery.domain.prediction import ActivityPrediction


class InMemoryCandidateRepository:
    def __init__(
        self,
        candidates: list[ActivityPrediction] | None = None,
    ) -> None:
        self._candidates = {
            prediction.compound.compound_id: prediction
            for prediction in candidates or []
        }

    def get(self, compound_id: str) -> ActivityPrediction | None:
        return self._candidates.get(compound_id)