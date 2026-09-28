from pathlib import Path

import pytest

from egfr_discovery.adapters.outbound.chemistry.rdkit_descriptors import (
    RDKitDescriptorCalculator,
)
from egfr_discovery.adapters.outbound.chemistry.rdkit_fingerprints import (
    RDKitFingerprintCalculator,
)
from egfr_discovery.adapters.outbound.ml.sklearn_activity_model import (
    SklearnActivityModel,
)
from egfr_discovery.adapters.outbound.persistence.csv_screening_library import (
    CsvScreeningLibrarySource,
)
from egfr_discovery.adapters.outbound.persistence.filesystem_screening_artifacts import (
    FilesystemScreeningArtifacts,
)
from egfr_discovery.application.dto.external_bioactivity import (
    ExternalBioactivityRecord,
)
from egfr_discovery.application.dto.screening import ScreeningPipelineCommand
from egfr_discovery.application.use_cases.calculate_compound_properties import (
    CalculateCompoundProperties,
)
from egfr_discovery.application.use_cases.curate_bioactivity_dataset import (
    CurateBioactivityDataset,
    NoAcceptedBioactivityRecords,
)
from egfr_discovery.application.use_cases.filter_candidates import FilterCandidates
from egfr_discovery.application.use_cases.import_screening_library import (
    ImportScreeningLibrary,
)
from egfr_discovery.application.use_cases.rank_candidates import RankCandidates
from egfr_discovery.application.use_cases.run_screening_pipeline import (
    RunScreeningPipeline,
)
from egfr_discovery.application.use_cases.screen_compounds import ScreenCompounds
from egfr_discovery.application.use_cases.select_diverse_candidates import (
    SelectDiverseCandidates,
)
from egfr_discovery.application.use_cases.split_bioactivity_dataset import (
    SplitBioactivityDataset,
)
from egfr_discovery.application.use_cases.train_activity_model import TrainActivityModel
from egfr_discovery.application.use_cases.validate_activity_model import (
    ValidateActivityModel,
)
from egfr_discovery.domain.exceptions import ModelValidationFailed


class FakeBioactivitySource:
    def fetch(
        self, *, target_id: str, activity_type: str
    ) -> list[ExternalBioactivityRecord]:
        smiles = ["CC", "CCC", "CCCC", "CCO", "CCN", "CCCl", "CCBr", "CCF"]
        return [
            ExternalBioactivityRecord(
                activity_id=index,
                compound_id=f"CHEMBL{index}",
                target_id=target_id,
                assay_id=f"ASSAY{index}",
                activity_type=activity_type,
                relation="=",
                value=str(10 ** (9 - (6.8 + index / 10))),
                units="nM",
                smiles=value,
                target_confidence=9,
            )
            for index, value in enumerate(smiles, start=1)
        ]


def build_pipeline(
    tmp_path: Path,
    *,
    source: FakeBioactivitySource | None = None,
    max_mae: float = 10.0,
) -> RunScreeningPipeline:
    model = SklearnActivityModel(n_estimators=8, random_seed=7)
    fingerprints = RDKitFingerprintCalculator()
    return RunScreeningPipeline(
        source=source or FakeBioactivitySource(),
        curate=CurateBioactivityDataset(fingerprints),
        split=SplitBioactivityDataset(validation_fraction=0.25, random_seed=7),
        train=TrainActivityModel(model, model_directory=tmp_path / "models"),
        validate=ValidateActivityModel(model, max_mae=max_mae),
        import_library=ImportScreeningLibrary(CsvScreeningLibrarySource()),
        screen=ScreenCompounds(model),
        calculate_properties=CalculateCompoundProperties(RDKitDescriptorCalculator()),
        filter_candidates=FilterCandidates(min_pic50=0.0),
        select_diverse=SelectDiverseCandidates(fingerprints),
        rank=RankCandidates(),
        artifacts=FilesystemScreeningArtifacts(tmp_path),
    )


def write_library(tmp_path: Path) -> Path:
    library_path = tmp_path / "library.csv"
    library_path.write_text(
        "compound_id,smiles\nLIB-1,CCO\nLIB-2,CCN\nLIB-3,c1ccccc1\n",
        encoding="utf-8",
    )
    return library_path


def test_pipeline_runs_end_to_end_without_live_network(tmp_path: Path) -> None:
    library_path = write_library(tmp_path)
    pipeline = build_pipeline(tmp_path)

    result = pipeline.execute(
        ScreeningPipelineCommand(
            library_path=library_path,
            output_path=tmp_path / "ranked.csv",
            max_validation_mae=10.0,
            shortlist_size=10,
        )
    )

    assert result.fetched_count == 8
    assert result.curated_count == 8
    assert result.rejected_count == 0
    assert result.screened_count == 3
    assert result.filtered_count == 3
    assert result.diverse_count == 3
    assert len(result.ranked_candidates) == 3
    assert result.validation.passed
    assert all(Path(path).exists() for path in result.artifact_paths)
    assert "not experimentally validated" in result.disclaimer


def test_pipeline_stops_before_screening_when_validation_fails(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "ranked-failed.csv"
    pipeline = build_pipeline(tmp_path, max_mae=1e-9)

    with pytest.raises(ModelValidationFailed):
        pipeline.execute(
            ScreeningPipelineCommand(
                library_path=write_library(tmp_path),
                output_path=output_path,
            )
        )

    assert not output_path.exists()


def test_pipeline_writes_rejections_when_every_record_is_rejected(
    tmp_path: Path,
) -> None:
    class InvalidSource(FakeBioactivitySource):
        def fetch(
            self, *, target_id: str, activity_type: str
        ) -> list[ExternalBioactivityRecord]:
            record = super().fetch(
                target_id=target_id,
                activity_type=activity_type,
            )[0]
            return [
                ExternalBioactivityRecord(
                    activity_id=record.activity_id,
                    compound_id=record.compound_id,
                    target_id=record.target_id,
                    assay_id=record.assay_id,
                    activity_type=record.activity_type,
                    relation=record.relation,
                    value=record.value,
                    units=record.units,
                    smiles="invalid",
                    target_confidence=record.target_confidence,
                )
            ]

    pipeline = build_pipeline(tmp_path, source=InvalidSource())

    with pytest.raises(NoAcceptedBioactivityRecords):
        pipeline.execute(ScreeningPipelineCommand(library_path=write_library(tmp_path)))

    report = tmp_path / "artifacts/reports/chembl203-ic50-curation.json"
    assert report.exists()
    assert '"reason": "invalid_smiles"' in report.read_text(encoding="utf-8")
