from egfr_discovery.application.dto.screening import EvaluatedCandidate
from egfr_discovery.application.ports.molecular_descriptors import (
    MolecularDescriptorCalculator,
)
from egfr_discovery.domain.candidate import CandidateProperties
from egfr_discovery.domain.prediction import ActivityPrediction


class CalculateCompoundProperties:
    def __init__(self, calculator: MolecularDescriptorCalculator) -> None:
        self._calculator = calculator

    def execute(
        self, predictions: list[ActivityPrediction]
    ) -> list[EvaluatedCandidate]:
        results: list[EvaluatedCandidate] = []

        for prediction in predictions:
            descriptors = self._calculator.calculate(prediction.compound.smiles)

            properties = CandidateProperties(
                molecular_weight=descriptors.molecular_weight,
                log_p=descriptors.log_p,
                hydrogen_bond_donors=descriptors.hydrogen_bond_donors,
                hydrogen_bond_acceptors=descriptors.hydrogen_bond_acceptors,
                polar_surface_area=descriptors.polar_surface_area,
            )

            results.append(
                EvaluatedCandidate(
                    prediction=prediction,
                    properties=properties,
                )
            )

        return results
