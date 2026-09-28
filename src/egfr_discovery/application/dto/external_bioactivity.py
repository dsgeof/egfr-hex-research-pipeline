from dataclasses import dataclass

from egfr_discovery.domain.dataset import CuratedDataset


@dataclass(frozen=True, slots=True)
class ExternalBioactivityRecord:
    activity_id: int | None
    compound_id: str
    target_id: str | None
    assay_id: str | None
    activity_type: str | None
    relation: str | None
    value: str | float | None
    units: str | None
    smiles: str | None
    target_confidence: int | None
    source: str = "ChEMBL"


@dataclass(frozen=True, slots=True)
class RejectedBioactivityRecord:
    record: ExternalBioactivityRecord
    reason: str


@dataclass(frozen=True, slots=True)
class CurationResult:
    dataset: CuratedDataset
    rejected: tuple[RejectedBioactivityRecord, ...]
