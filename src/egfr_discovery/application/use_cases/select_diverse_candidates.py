from egfr_discovery.application.dto.screening import EvaluatedCandidate
from egfr_discovery.application.ports.molecular_fingerprints import (
    MolecularFingerprintCalculator,
)


class SelectDiverseCandidates:
    def __init__(
        self,
        fingerprints: MolecularFingerprintCalculator,
        similarity_threshold: float = 0.7,
    ) -> None:
        self._fingerprints = fingerprints
        self._threshold = similarity_threshold

    def execute(
        self,
        candidates: list[EvaluatedCandidate],
        max_candidates: int = 100,
    ) -> list[EvaluatedCandidate]:
        candidates = sorted(
            candidates,
            key=lambda candidate: candidate.prediction.predicted_pic50,
            reverse=True,
        )

        selected: list[EvaluatedCandidate] = []
        selected_fingerprints: list[object] = []

        for candidate in candidates:
            fingerprint = self._fingerprints.fingerprint(
                candidate.prediction.compound.smiles
            )

            sufficiently_different = all(
                self._fingerprints.similarity(fingerprint, existing) < self._threshold
                for existing in selected_fingerprints
            )

            if sufficiently_different:
                selected.append(candidate)
                selected_fingerprints.append(fingerprint)

            if len(selected) >= max_candidates:
                break

        return selected
