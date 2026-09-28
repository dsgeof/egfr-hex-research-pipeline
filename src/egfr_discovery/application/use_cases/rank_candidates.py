from egfr_discovery.application.dto.screening import (
    EvaluatedCandidate,
    RankedCandidate,
)


class RankCandidates:
    def execute(
        self,
        candidates: list[EvaluatedCandidate],
        source_library_id: str,
    ) -> list[RankedCandidate]:
        scored: list[tuple[EvaluatedCandidate, float]] = []
        for candidate in candidates:
            prediction = candidate.prediction
            properties = candidate.properties
            potency_score = min(
                max((prediction.predicted_pic50 - 5.0) / 4.0, 0.0),
                1.0,
            )
            property_score = 1.0
            if properties.molecular_weight > 500:
                property_score -= 0.2
            if properties.log_p > 4.5:
                property_score -= 0.2
            if properties.polar_surface_area > 140:
                property_score -= 0.2

            uncertainty = (
                prediction.uncertainty if prediction.uncertainty is not None else 0.5
            )
            confidence_score = max(0.0, 1.0 - uncertainty)
            score = (
                0.70 * potency_score + 0.20 * property_score + 0.10 * confidence_score
            )
            scored.append((candidate, score))

        scored.sort(
            key=lambda item: (
                -item[1],
                item[0].prediction.compound.compound_id,
            )
        )
        return [
            RankedCandidate(
                rank=rank,
                compound_id=candidate.prediction.compound.compound_id,
                smiles=candidate.prediction.compound.smiles,
                predicted_pic50=candidate.prediction.predicted_pic50,
                uncertainty=candidate.prediction.uncertainty,
                properties=candidate.properties,
                score=score,
                source_library_id=source_library_id,
            )
            for rank, (candidate, score) in enumerate(scored, start=1)
        ]
