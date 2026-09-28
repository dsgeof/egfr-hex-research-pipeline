from egfr_discovery.adapters.outbound.chembl.bioactivity_source_data import (
    ChEMBLBioactivitySource,
)
from egfr_discovery.adapters.outbound.chembl.client import ChEMBLClient
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
from egfr_discovery.application.dto.screening import (
    ScreeningPipelineCommand,
    ScreeningPipelineResult,
)
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
from egfr_discovery.config import get_settings


def build_screening_pipeline(
    client: ChEMBLClient,
    command: ScreeningPipelineCommand,
) -> RunScreeningPipeline:
    model = SklearnActivityModel(random_seed=command.random_seed)
    fingerprints = RDKitFingerprintCalculator()
    return RunScreeningPipeline(
        source=ChEMBLBioactivitySource(client),
        curate=CurateBioactivityDataset(fingerprints),
        split=SplitBioactivityDataset(
            validation_fraction=command.validation_fraction,
            random_seed=command.random_seed,
        ),
        train=TrainActivityModel(model),
        validate=ValidateActivityModel(model, command.max_validation_mae),
        import_library=ImportScreeningLibrary(CsvScreeningLibrarySource()),
        screen=ScreenCompounds(model),
        calculate_properties=CalculateCompoundProperties(RDKitDescriptorCalculator()),
        filter_candidates=FilterCandidates(),
        select_diverse=SelectDiverseCandidates(
            fingerprints,
            similarity_threshold=command.similarity_threshold,
        ),
        rank=RankCandidates(),
        artifacts=FilesystemScreeningArtifacts(),
    )


def run_pipeline(command: ScreeningPipelineCommand) -> ScreeningPipelineResult:
    base_url = str(get_settings().chembl_client_base_url)
    with ChEMBLClient(base_url) as client:
        pipeline = build_screening_pipeline(client, command)
        return pipeline.execute(command)
