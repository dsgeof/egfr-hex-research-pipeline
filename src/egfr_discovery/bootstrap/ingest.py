from egfr_discovery.adapters.outbound.chembl.bioactivity_source_data import (
    ChEMBLBioactivitySource,
)
from egfr_discovery.adapters.outbound.chembl.client import (
    ChEMBLClient,
)
from egfr_discovery.application.use_cases.ingest_bioactivity_data import (
    IngestBioactivityDataset,
)


def build_ingestion_use_case() -> IngestBioactivityDataset:

    client = ChEMBLClient()

    source = ChEMBLBioactivitySource(
        client=client
    )

    return IngestBioactivityDataset(
        source=source
    )