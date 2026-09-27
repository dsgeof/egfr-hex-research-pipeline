from typing import Protocol
from egfr_discovery.adapters.outbound.chembl.models import (
    ChEMBLActivityRecord,
)


class BioactivitySource(Protocol):
    def fetch(
        self,
        *,
        target_id: str,
        activity_type: str,
    ) -> list[ChEMBLActivityRecord]:
        ...