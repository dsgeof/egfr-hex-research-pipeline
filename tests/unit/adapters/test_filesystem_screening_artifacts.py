import csv
import json
from decimal import Decimal
from pathlib import Path

from egfr_discovery.adapters.outbound.persistence.filesystem_screening_artifacts import (
    FilesystemScreeningArtifacts,
)
from egfr_discovery.application.dto.external_bioactivity import (
    CurationResult,
    ExternalBioactivityRecord,
    RejectedBioactivityRecord,
)
from egfr_discovery.application.dto.screening import RankedCandidate
from egfr_discovery.domain.bioactivity import BioactivityMeasurement
from egfr_discovery.domain.candidate import CandidateProperties
from egfr_discovery.domain.dataset import CuratedDataset


def external_record(value: str = "10.0") -> ExternalBioactivityRecord:
    return ExternalBioactivityRecord(
        activity_id=1,
        compound_id="CHEMBL1",
        target_id="CHEMBL203",
        assay_id="CHEMBL-A1",
        activity_type="IC50",
        relation="=",
        value=value,
        units="nM",
        smiles="CCO",
        target_confidence=9,
    )


def test_artifacts_preserve_raw_curation_and_ranked_evidence(tmp_path: Path) -> None:
    artifacts = FilesystemScreeningArtifacts(tmp_path)
    record = external_record()
    raw_path = artifacts.save_raw([record], "CHEMBL203")
    curation = CurationResult(
        dataset=CuratedDataset(
            "dataset",
            (
                BioactivityMeasurement(
                    1,
                    "CHEMBL1",
                    "CHEMBL-A1",
                    "CHEMBL203",
                    "CCO",
                    Decimal("10.0"),
                ),
            ),
        ),
        rejected=(RejectedBioactivityRecord(record, "invalid_smiles"),),
    )
    processed_path, report_path = artifacts.save_curation(curation)
    ranked_path = artifacts.save_ranked(
        [
            RankedCandidate(
                rank=1,
                compound_id="LIB-1",
                smiles="CCN",
                predicted_pic50=7.4,
                uncertainty=0.2,
                properties=CandidateProperties(45.1, -0.1, 1, 1, 26.0),
                score=0.8,
                source_library_id="library",
            )
        ],
        tmp_path / "ranked.csv",
        "research disclaimer",
    )

    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    with processed_path.open(encoding="utf-8") as handle:
        processed = list(csv.DictReader(handle))
    with ranked_path.open(encoding="utf-8") as handle:
        ranked = list(csv.DictReader(handle))

    assert raw["metadata"]["target_id"] == "CHEMBL203"
    assert raw["records"][0]["value"] == "10.0"
    assert report["rejected"][0]["reason"] == "invalid_smiles"
    assert processed[0]["ic50_nm"] == "10.0"
    assert processed[0]["assay_id"] == "CHEMBL-A1"
    assert ranked[0]["compound_id"] == "LIB-1"
    assert ranked[0]["source_library_id"] == "library"
    assert ranked[0]["disclaimer"] == "research disclaimer"


def test_curation_failure_report_preserves_every_rejection(tmp_path: Path) -> None:
    artifacts = FilesystemScreeningArtifacts(tmp_path)
    rejected = (
        RejectedBioactivityRecord(external_record(), "invalid_smiles"),
        RejectedBioactivityRecord(external_record("0"), "non_positive_value"),
    )

    report_path = artifacts.save_curation_failure("dataset", rejected)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["accepted_count"] == 0
    assert report["rejected_count"] == 2
    assert [item["reason"] for item in report["rejected"]] == [
        "invalid_smiles",
        "non_positive_value",
    ]
