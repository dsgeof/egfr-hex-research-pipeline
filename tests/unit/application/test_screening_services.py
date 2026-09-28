from egfr_discovery.application.ports.molecular_descriptors import MolecularDescriptors
from egfr_discovery.application.use_cases.calculate_compound_properties import (
    CalculateCompoundProperties,
)
from egfr_discovery.application.use_cases.filter_candidates import FilterCandidates
from egfr_discovery.application.use_cases.rank_candidates import RankCandidates
from egfr_discovery.application.use_cases.select_diverse_candidates import (
    SelectDiverseCandidates,
)
from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.prediction import ActivityPrediction


class StubDescriptors:
    def calculate(self, smiles: str) -> MolecularDescriptors:
        return MolecularDescriptors(300.0, 2.0, 1, 2, 60.0)


class StubFingerprints:
    def fingerprint(self, smiles: str) -> object:
        return smiles

    def similarity(self, left: object, right: object) -> float:
        return 1.0 if left == right else 0.0


def predictions() -> list[ActivityPrediction]:
    return [
        ActivityPrediction(Compound("CMP-1", "CCO"), 7.2, 0.1),
        ActivityPrediction(Compound("CMP-2", "CCN"), 8.1, 0.2),
        ActivityPrediction(Compound("CMP-3", "CCO"), 7.8, 0.3),
    ]


def test_services_retain_evidence_and_rank_stably() -> None:
    evaluated = CalculateCompoundProperties(StubDescriptors()).execute(predictions())
    filtered = FilterCandidates(min_pic50=7.0).execute(evaluated)
    diverse = SelectDiverseCandidates(
        StubFingerprints(), similarity_threshold=0.7
    ).execute(filtered, max_candidates=10)
    ranked = RankCandidates().execute(diverse, source_library_id="library")

    assert [item.compound_id for item in ranked] == ["CMP-2", "CMP-3"]
    assert ranked[0].smiles == "CCN"
    assert ranked[0].predicted_pic50 == 8.1
    assert ranked[0].uncertainty == 0.2
    assert ranked[0].properties.molecular_weight == 300.0
    assert ranked[0].source_library_id == "library"
    assert [item.rank for item in ranked] == [1, 2]


def test_filter_thresholds_are_configurable() -> None:
    evaluated = CalculateCompoundProperties(StubDescriptors()).execute(predictions())

    assert FilterCandidates(min_pic50=8.0).execute(evaluated) == [evaluated[1]]
