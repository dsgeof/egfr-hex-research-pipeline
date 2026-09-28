from pathlib import Path
from typing import ClassVar, Self

import pytest

from egfr_discovery.adapters.outbound.chembl.bioactivity_source_data import (
    ChEMBLBioactivitySource,
)
from egfr_discovery.adapters.outbound.persistence.filesystem_screening_artifacts import (
    FilesystemScreeningArtifacts,
)
from egfr_discovery.application.dto.screening import ScreeningPipelineCommand
from egfr_discovery.application.use_cases.calculate_compound_properties import (
    CalculateCompoundProperties,
)
from egfr_discovery.application.use_cases.curate_bioactivity_dataset import (
    CurateBioactivityDataset,
)
from egfr_discovery.application.use_cases.filter_candidates import FilterCandidates
from egfr_discovery.application.use_cases.import_screening_library import (
    ImportScreeningLibrary,
)
from egfr_discovery.application.use_cases.rank_candidates import RankCandidates
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
from egfr_discovery.bootstrap import screening_pipeline


class FakeClient:
    instances: ClassVar[list[FakeClient]] = []

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.closed = False
        self.instances.append(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self.closed = True


def test_builder_shares_one_model_across_model_use_cases(tmp_path: Path) -> None:
    command = ScreeningPipelineCommand(library_path=tmp_path / "library.csv")
    pipeline = screening_pipeline.build_screening_pipeline(FakeClient("test"), command)

    assert pipeline._train._model is pipeline._validate._model
    assert pipeline._train._model is pipeline._screen._model
    assert isinstance(pipeline._source, ChEMBLBioactivitySource)
    assert isinstance(pipeline._curate, CurateBioactivityDataset)
    assert isinstance(pipeline._split, SplitBioactivityDataset)
    assert isinstance(pipeline._train, TrainActivityModel)
    assert isinstance(pipeline._validate, ValidateActivityModel)
    assert isinstance(pipeline._import_library, ImportScreeningLibrary)
    assert isinstance(pipeline._screen, ScreenCompounds)
    assert isinstance(pipeline._calculate_properties, CalculateCompoundProperties)
    assert isinstance(pipeline._filter_candidates, FilterCandidates)
    assert isinstance(pipeline._select_diverse, SelectDiverseCandidates)
    assert isinstance(pipeline._rank, RankCandidates)
    assert isinstance(pipeline._artifacts, FilesystemScreeningArtifacts)


@pytest.mark.parametrize("raises", [False, True])
def test_run_pipeline_closes_client_on_success_and_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    raises: bool,
) -> None:
    class StubPipeline:
        def execute(self, command: ScreeningPipelineCommand) -> object:
            if raises:
                raise RuntimeError("failed")
            return object()

    FakeClient.instances.clear()
    monkeypatch.setattr(screening_pipeline, "ChEMBLClient", FakeClient)
    monkeypatch.setattr(
        screening_pipeline,
        "build_screening_pipeline",
        lambda client, command: StubPipeline(),
    )
    command = ScreeningPipelineCommand(library_path=tmp_path / "library.csv")

    if raises:
        with pytest.raises(RuntimeError, match="failed"):
            screening_pipeline.run_pipeline(command)
    else:
        screening_pipeline.run_pipeline(command)

    assert FakeClient.instances[0].closed
