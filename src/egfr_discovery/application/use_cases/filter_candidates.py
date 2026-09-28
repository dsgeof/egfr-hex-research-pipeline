from egfr_discovery.application.dto.screening import EvaluatedCandidate


class FilterCandidates:
    def __init__(
        self,
        min_pic50: float = 6.5,
        max_molecular_weight: float = 550.0,
        max_log_p: float = 5.0,
        max_polar_surface_area: float = 150.0,
    ) -> None:
        self._min_pic50 = min_pic50
        self._max_molecular_weight = max_molecular_weight
        self._max_log_p = max_log_p
        self._max_polar_surface_area = max_polar_surface_area

    def execute(self, candidates: list[EvaluatedCandidate]) -> list[EvaluatedCandidate]:

        accepted: list[EvaluatedCandidate] = []

        for candidate in candidates:
            prediction = candidate.prediction
            properties = candidate.properties

            if prediction.predicted_pic50 < self._min_pic50:
                continue
            if properties.molecular_weight > self._max_molecular_weight:
                continue
            if properties.log_p > self._max_log_p:
                continue
            if properties.polar_surface_area > self._max_polar_surface_area:
                continue

            accepted.append(candidate)

        return accepted
