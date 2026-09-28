from egfr_discovery.adapters.outbound.chembl.bioactivity_source_data import (
    ChEMBLBioactivitySource,
)
from egfr_discovery.adapters.outbound.chembl.client import (
    ChEMBLClient,
)
from egfr_discovery.adapters.outbound.chemistry.rdkit_fingerprints import (
    RDKitFingerprintCalculator,
)
from egfr_discovery.application.use_cases.ingest_bioactivity_data import (
    IngestBioactivityCommand,
    IngestBioactivityDataset,
    IngestionResult,
)
from egfr_discovery.config import get_settings


def build_ingestion_use_case(client: ChEMBLClient) -> IngestBioactivityDataset:
    source = ChEMBLBioactivitySource(client=client)
    return IngestBioactivityDataset(
        source=source,
        structure_validator=RDKitFingerprintCalculator(),
    )


def run_ingestion(command: IngestBioactivityCommand) -> IngestionResult:
    with ChEMBLClient(str(get_settings().chembl_client_base_url)) as client:
        return build_ingestion_use_case(client).execute(command)
