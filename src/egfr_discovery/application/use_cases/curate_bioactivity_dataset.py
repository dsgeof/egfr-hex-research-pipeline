from dataclasses import dataclass

from egfr_discovery.application.dto.external_bioactivity import (
    ExternalBioactivityRecord,
)
from egfr_discovery.domain.bioactivity import BioactivityMeasurement
from egfr_discovery.domain.dataset import CuratedDataset


@dataclass(frozen=True, slots=True)
class CurateBioactivityCommand:
    dataset_id: str
    records: list[ExternalBioactivityRecord]


class CurateBioactivityDataset:
    def execute(self, command: CurateBioactivityCommand) -> CuratedDataset:
        measurements: list[BioactivityMeasurement] = []

        for record in command.records:
            if record.activity_type != "IC50":
                continue
            if record.relation != "=":
                continue
            if record.units != "nM":
                continue
            if record.value is None:
                continue
            if not record.smiles:
                continue
            if "." in record.smiles:
                continue

            value_nm = float(record.value)

            if value_nm <= 0:
                continue

            measurement = BioactivityMeasurement(
                activity_id=record.activity_id,
                compound_id=record.compound_id,
                assay_id=record.assay_id,
                target_id=record.target_id,
                smiles=record.smiles,
                ic50_nm=value_nm,
            )

            measurements.append(measurement)

        return CuratedDataset(
            dataset_id=command.dataset_id,
            measurements=tuple(measurements),
        )