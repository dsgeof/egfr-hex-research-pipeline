from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from egfr_discovery.application.dto.external_bioactivity import (
    CurationResult,
    ExternalBioactivityRecord,
    RejectedBioactivityRecord,
)
from egfr_discovery.application.ports.molecular_structure import (
    MolecularStructureValidator,
)
from egfr_discovery.domain.bioactivity import BioactivityMeasurement
from egfr_discovery.domain.dataset import CuratedDataset


@dataclass(frozen=True, slots=True)
class CurateBioactivityCommand:
    dataset_id: str
    records: list[ExternalBioactivityRecord]
    activity_type: str = "IC50"
    units: str = "nM"
    relation: str = "="


class NoAcceptedBioactivityRecords(ValueError):
    def __init__(
        self,
        dataset_id: str,
        rejected: tuple[RejectedBioactivityRecord, ...],
    ) -> None:
        super().__init__("Curation produced no acceptable records")
        self.dataset_id = dataset_id
        self.rejected = rejected


class CurateBioactivityDataset:
    def __init__(self, structure_validator: MolecularStructureValidator) -> None:
        self._structure_validator = structure_validator

    def execute(self, command: CurateBioactivityCommand) -> CurationResult:
        measurements: list[BioactivityMeasurement] = []
        rejected: list[RejectedBioactivityRecord] = []

        for record in command.records:
            reason = self._rejection_reason(record, command)
            if reason is not None:
                rejected.append(RejectedBioactivityRecord(record=record, reason=reason))
                continue

            assert record.activity_id is not None
            assert record.assay_id is not None
            assert record.target_id is not None
            assert record.smiles is not None
            assert record.value is not None
            measurements.append(
                BioactivityMeasurement(
                    activity_id=record.activity_id,
                    compound_id=record.compound_id,
                    assay_id=record.assay_id,
                    target_id=record.target_id,
                    smiles=record.smiles,
                    ic50_nm=Decimal(str(record.value)),
                    source=record.source,
                )
            )

        if not measurements:
            raise NoAcceptedBioactivityRecords(command.dataset_id, tuple(rejected))

        return CurationResult(
            dataset=CuratedDataset(command.dataset_id, tuple(measurements)),
            rejected=tuple(rejected),
        )

    def _rejection_reason(
        self,
        record: ExternalBioactivityRecord,
        command: CurateBioactivityCommand,
    ) -> str | None:
        if record.activity_id is None:
            return "missing_activity_id"
        if not record.compound_id.strip():
            return "missing_compound_id"
        if record.assay_id is None or not record.assay_id.strip():
            return "missing_assay_id"
        if record.target_id is None or not record.target_id.strip():
            return "missing_target_id"
        if record.activity_type != command.activity_type:
            return "wrong_activity_type"
        if record.relation != command.relation:
            return "non_exact_relation"
        if record.units != command.units:
            return "wrong_units"
        if record.value is None:
            return "missing_value"
        try:
            value = Decimal(str(record.value))
        except InvalidOperation:
            return "invalid_value"
        if not value.is_finite():
            return "invalid_value"
        if value <= 0:
            return "non_positive_value"
        if not record.smiles:
            return "missing_smiles"
        if "." in record.smiles:
            return "mixture"
        if not self._structure_validator.is_valid(record.smiles):
            return "invalid_smiles"
        return None
