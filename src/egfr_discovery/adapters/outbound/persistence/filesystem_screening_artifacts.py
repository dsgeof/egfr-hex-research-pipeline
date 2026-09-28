import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from egfr_discovery.application.dto.external_bioactivity import (
    CurationResult,
    ExternalBioactivityRecord,
    RejectedBioactivityRecord,
)
from egfr_discovery.application.dto.screening import RankedCandidate


class FilesystemScreeningArtifacts:
    def __init__(self, base_directory: Path = Path(".")) -> None:
        self._base_directory = base_directory

    def save_raw(
        self,
        records: list[ExternalBioactivityRecord],
        target_id: str,
    ) -> Path:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        destination = (
            self._base_directory
            / "data"
            / "raw"
            / f"chembl_{target_id}_{timestamp}.json"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(
                {
                    "metadata": {
                        "source": "ChEMBL",
                        "target_id": target_id,
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
        return destination

    def save_curation(self, result: CurationResult) -> tuple[Path, Path]:
        processed = (
            self._base_directory
            / "data"
            / "processed"
            / f"{result.dataset.dataset_id}.csv"
        )
        report = (
            self._base_directory
            / "artifacts"
            / "reports"
            / f"{result.dataset.dataset_id}-curation.json"
        )
        processed.parent.mkdir(parents=True, exist_ok=True)
        report.parent.mkdir(parents=True, exist_ok=True)
        with processed.open("w", newline="", encoding="utf-8") as handle:
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
            for measurement in result.dataset.measurements:
                writer.writerow(
                    {
                        **asdict(measurement),
                        "ic50_nm": str(measurement.ic50_nm),
                    }
                )
        report.write_text(
            json.dumps(
                {
                    "dataset_id": result.dataset.dataset_id,
                    "accepted_count": len(result.dataset.measurements),
                    "rejected_count": len(result.rejected),
                    "rejected": [asdict(item) for item in result.rejected],
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return processed, report

    def save_curation_failure(
        self,
        dataset_id: str,
        rejected: tuple[RejectedBioactivityRecord, ...],
    ) -> Path:
        report = (
            self._base_directory
            / "artifacts"
            / "reports"
            / f"{dataset_id}-curation.json"
        )
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(
                {
                    "dataset_id": dataset_id,
                    "accepted_count": 0,
                    "rejected_count": len(rejected),
                    "rejected": [asdict(item) for item in rejected],
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return report

    def save_ranked(
        self,
        candidates: list[RankedCandidate],
        destination: Path,
        disclaimer: str,
    ) -> Path:
        path = (
            destination
            if destination.is_absolute()
            else self._base_directory / destination
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "rank",
            "compound_id",
            "smiles",
            "predicted_pic50",
            "uncertainty",
            "molecular_weight",
            "log_p",
            "hydrogen_bond_donors",
            "hydrogen_bond_acceptors",
            "polar_surface_area",
            "score",
            "source_library_id",
            "disclaimer",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for candidate in candidates:
                writer.writerow(
                    {
                        "rank": candidate.rank,
                        "compound_id": candidate.compound_id,
                        "smiles": candidate.smiles,
                        "predicted_pic50": candidate.predicted_pic50,
                        "uncertainty": candidate.uncertainty,
                        **asdict(candidate.properties),
                        "score": candidate.score,
                        "source_library_id": candidate.source_library_id,
                        "disclaimer": disclaimer,
                    }
                )
        return path
