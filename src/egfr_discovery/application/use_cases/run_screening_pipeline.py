import logging

from egfr_discovery.application.dto.screening import (
    ScreeningPipelineCommand,
    ScreeningPipelineResult,
)
from egfr_discovery.application.ports.bioactivity_source_data import BioactivitySource
from egfr_discovery.application.ports.screening_artifacts import ScreeningArtifacts
from egfr_discovery.application.use_cases.calculate_compound_properties import (
    CalculateCompoundProperties,
)
from egfr_discovery.application.use_cases.curate_bioactivity_dataset import (
    CurateBioactivityCommand,
    CurateBioactivityDataset,
    NoAcceptedBioactivityRecords,
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
from egfr_discovery.domain.exceptions import ModelValidationFailed

RESEARCH_DISCLAIMER = (
    "Research prediction only; candidates are not experimentally validated "
    "medicines or clinical recommendations."
)


class RunScreeningPipeline:
    def __init__(
        self,
        *,
        source: BioactivitySource,
        curate: CurateBioactivityDataset,
        split: SplitBioactivityDataset,
        train: TrainActivityModel,
        validate: ValidateActivityModel,
        import_library: ImportScreeningLibrary,
        screen: ScreenCompounds,
        calculate_properties: CalculateCompoundProperties,
        filter_candidates: FilterCandidates,
        select_diverse: SelectDiverseCandidates,
        rank: RankCandidates,
        artifacts: ScreeningArtifacts,
        logger: logging.Logger | None = None,
    ) -> None:
        self._source = source
        self._curate = curate
        self._split = split
        self._train = train
        self._validate = validate
        self._import_library = import_library
        self._screen = screen
        self._calculate_properties = calculate_properties
        self._filter_candidates = filter_candidates
        self._select_diverse = select_diverse
        self._rank = rank
        self._artifacts = artifacts
        self._logger = logger or logging.getLogger(__name__)

    def execute(self, command: ScreeningPipelineCommand) -> ScreeningPipelineResult:
        self._logger.info("Fetching bioactivity records")
        records = self._source.fetch(
            target_id=command.target_id,
            activity_type=command.activity_type,
        )
        raw_path = self._artifacts.save_raw(records, command.target_id)

        self._logger.info("Curating %d bioactivity records", len(records))
        dataset_id = f"{command.target_id.lower()}-{command.activity_type.lower()}"
        try:
            curation = self._curate.execute(
                CurateBioactivityCommand(
                    dataset_id=dataset_id,
                    records=records,
                    activity_type=command.activity_type,
                )
            )
        except NoAcceptedBioactivityRecords as error:
            self._artifacts.save_curation_failure(
                error.dataset_id,
                error.rejected,
            )
            raise
        processed_path, report_path = self._artifacts.save_curation(curation)

        self._logger.info("Splitting, training, and validating activity model")
        split = self._split.execute(curation.dataset)
        self._train.execute(split.train)
        validation = self._validate.execute(split.validation)
        if not validation.passed:
            raise ModelValidationFailed(validation.failures)

        self._logger.info("Importing and screening compound library")
        library = self._import_library.execute(str(command.library_path))
        predictions = self._screen.execute(library)
        evaluated = self._calculate_properties.execute(predictions)
        filtered = self._filter_candidates.execute(evaluated)
        diverse = self._select_diverse.execute(
            filtered,
            max_candidates=command.shortlist_size,
        )
        ranked = self._rank.execute(diverse, source_library_id=library.library_id)
        ranked_path = self._artifacts.save_ranked(
            ranked,
            command.output_path,
            RESEARCH_DISCLAIMER,
        )
        self._logger.info("Screening complete: %d ranked candidates", len(ranked))

        return ScreeningPipelineResult(
            fetched_count=len(records),
            curated_count=len(curation.dataset.measurements),
            rejected_count=len(curation.rejected),
            screened_count=len(predictions),
            filtered_count=len(filtered),
            diverse_count=len(diverse),
            validation=validation,
            ranked_candidates=tuple(ranked),
            artifact_paths=(
                str(raw_path),
                str(processed_path),
                str(report_path),
                str(ranked_path),
            ),
            disclaimer=RESEARCH_DISCLAIMER,
        )
