from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation
import json
from datetime import UTC, datetime
from pathlib import Path
import csv

from rdkit import Chem

from egfr_discovery.adapters.outbound.chembl.models import (
    ChEMBLActivityRecord,
)
from egfr_discovery.domain.bioactivity import (
    BioactivityMeasurement,
)


@dataclass(slots=True)
class CurationReport:
    total_records: int = 0

    accepted: int = 0

    wrong_activity_type: int = 0
    non_exact_relation: int = 0
    wrong_units: int = 0
    missing_value: int = 0

    missing_smiles: int = 0
    invalid_smiles: int = 0
    mixtures: int = 0

    missing_assay: int = 0
    low_target_confidence: int = 0

    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CurationPolicy:
    activity_type: str = "IC50"
    units: str = "nM"
    relation: str = "="

    minimum_target_confidence: int = 8


def curate_record(
    record: ChEMBLActivityRecord,
    policy: CurationPolicy,
    report: CurationReport,
) -> BioactivityMeasurement | None:

    if record.standard_type != policy.activity_type:
        report.wrong_activity_type += 1
        return None

    if record.standard_relation != policy.relation:
        report.non_exact_relation += 1
        return None

    if record.standard_units != policy.units:
        report.wrong_units += 1
        return None

    if record.standard_value is None:
        report.missing_value += 1
        return None

    if record.assay_chembl_id is None:
        report.missing_assay += 1
        return None

    if (
        record.confidence_score is not None
        and record.confidence_score
        < policy.minimum_target_confidence
    ):
        report.low_target_confidence += 1
        return None

    smiles = record.canonical_smiles

    if not smiles:
        report.missing_smiles += 1
        return None

    if "." in smiles:
        report.mixtures += 1
        return None

    molecule = Chem.MolFromSmiles(smiles)

    if molecule is None:
        report.invalid_smiles += 1
        return None

    try:
        value = Decimal(str(record.standard_value))
    except InvalidOperation:
        report.errors.append(
            f"Invalid activity value: {record.standard_value}"
        )
        return None

    if value <= 0:
        report.errors.append(
            f"Non-positive IC50: {value}"
        )
        return None

    if record.activity_id is None:
        report.errors.append(
            f"Missing activity id for "
            f"{record.molecule_chembl_id}"
        )
        return None

    return BioactivityMeasurement(
        activity_id=record.activity_id,
        compound_id=record.molecule_chembl_id,
        assay_id=record.assay_chembl_id,
        target_id=record.target_chembl_id or "",
        smiles=smiles,
        ic50_nm=value,
    )

def curate_dataset(
    records: list[ChEMBLActivityRecord],
    policy: CurationPolicy,
) -> tuple[list[BioactivityMeasurement], CurationReport]:

    report = CurationReport(
        total_records=len(records)
    )

    measurements: list[BioactivityMeasurement] = []

    for record in records:
        measurement = curate_record(
            record=record,
            policy=policy,
            report=report,
        )

        if measurement is not None:
            measurements.append(measurement)
            report.accepted += 1

    return measurements, report


def write_raw_snapshot(*, records: list[ChEMBLActivityRecord], directory: Path, target_id: str) -> Path:

    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    destination = (directory / f"chembl_{target_id}_{timestamp}.json")

    payload = {
        "metadata": {
            "source": "ChEMBL",
            "target_id": target_id,
            "retrieved_at": timestamp,
            "record_count": len(records),
        },
        "records": [
            record.model_dump()
            for record in records
        ],
    }

    destination.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )

    return destination


def write_processed_dataset(measurements: list[BioactivityMeasurement], destination: Path) -> None:

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "activity_id",
                "compound_id",
                "assay_id",
                "target_id",
                "smiles",
                "ic50_nm",
            ],
        )

        writer.writeheader()

        for measurement in measurements:
            writer.writerow(
                {
                    "activity_id":
                        measurement.activity_id,
                    "compound_id":
                        measurement.compound_id,
                    "assay_id":
                        measurement.assay_id,
                    "target_id":
                        measurement.target_id,
                    "smiles":
                        measurement.smiles,
                    "ic50_nm":
                        str(measurement.ic50_nm),
                }
            )

    return None

def write_quality_report(report: CurationReport, destination: Path) -> None:

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination.write_text(
        json.dumps(
            asdict(report),
            indent=2,
        ),
        encoding="utf-8",
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
        source,
    ) -> None:
        self._source = source

    def execute(
        self,
        command: IngestBioactivityCommand,
    ) -> IngestionResult:

        records = self._source.fetch(
            target_id=command.target_id,
            activity_type=command.activity_type,
        )

        raw_file = write_raw_snapshot(
            records=records,
            directory=Path("data/raw"),
            target_id=command.target_id,
        )

        policy = CurationPolicy(
            activity_type=command.activity_type,
        )

        measurements, report = curate_dataset(
            records=records,
            policy=policy,
        )

        processed_file = Path(
            "data/processed"
        ) / (
            f"{command.target_id.lower()}_"
            f"{command.activity_type.lower()}_"
            f"{command.dataset_version}.csv"
        )

        report_file = Path(
            "artifacts/reports"
        ) / (
            f"dataset_quality_"
            f"{command.dataset_version}.json"
        )

        write_processed_dataset(
            measurements,
            processed_file,
        )

        write_quality_report(
            report,
            report_file,
        )

        return IngestionResult(
            raw_file=raw_file,
            processed_file=processed_file,
            report_file=report_file,
            downloaded_records=len(records),
            accepted_records=len(measurements),
        )