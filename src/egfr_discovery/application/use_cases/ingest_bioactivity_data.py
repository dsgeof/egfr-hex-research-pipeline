import csv
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from egfr_discovery.application.ports.bioactivity_source_data import BioactivitySource
from egfr_discovery.application.ports.molecular_structure import (
    MolecularStructureValidator,
)
from egfr_discovery.application.use_cases.curate_bioactivity_dataset import (
    CurateBioactivityCommand,
    CurateBioactivityDataset,
)


@dataclass(frozen=True, slots=True)
class IngestBioactivityCommand:
    target_id: str
    activity_type: str
    dataset_version: str


@dataclass(frozen=True, slots=True)
class IngestionResult:
    raw_file: Path
    processed_file: Path
    report_file: Path
    downloaded_records: int
    accepted_records: int


class IngestBioactivityDataset:
    def __init__(
        self,
        source: BioactivitySource,
        structure_validator: MolecularStructureValidator,
    ) -> None:
        self._source = source
        self._curate = CurateBioactivityDataset(structure_validator)

    def execute(self, command: IngestBioactivityCommand) -> IngestionResult:
        records = self._source.fetch(
            target_id=command.target_id,
            activity_type=command.activity_type,
        )
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        raw_file = Path("data/raw") / f"chembl_{command.target_id}_{timestamp}.json"
        raw_file.parent.mkdir(parents=True, exist_ok=True)
        raw_file.write_text(
            json.dumps(
                {
                    "metadata": {
                        "source": "ChEMBL",
                        "target_id": command.target_id,
                        "retrieved_at": timestamp,
                        "record_count": len(records),
                    },
                    "records": [asdict(record) for record in records],
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        curation = self._curate.execute(
            CurateBioactivityCommand(
                dataset_id=command.dataset_version,
                records=records,
                activity_type=command.activity_type,
            )
        )
        processed_file = Path("data/processed") / (
            f"{command.target_id.lower()}_{command.activity_type.lower()}_"
            f"{command.dataset_version}.csv"
        )
        processed_file.parent.mkdir(parents=True, exist_ok=True)
        with processed_file.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = [
                "activity_id",
                "compound_id",
                "assay_id",
                "target_id",
                "smiles",
                "ic50_nm",
                "source",
            ]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for measurement in curation.dataset.measurements:
                writer.writerow(
                    {
                        **asdict(measurement),
                        "ic50_nm": str(measurement.ic50_nm),
                    }
                )

        report_file = (
            Path("artifacts/reports")
            / f"dataset_quality_{command.dataset_version}.json"
        )
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(
            json.dumps(
                {
                    "total_records": len(records),
                    "accepted": len(curation.dataset.measurements),
                    "rejected": [asdict(item) for item in curation.rejected],
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return IngestionResult(
            raw_file=raw_file,
            processed_file=processed_file,
            report_file=report_file,
            downloaded_records=len(records),
            accepted_records=len(curation.dataset.measurements),
        )
