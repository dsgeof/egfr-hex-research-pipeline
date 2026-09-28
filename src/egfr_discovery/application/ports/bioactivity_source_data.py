from typing import Protocol

from egfr_discovery.application.dto.external_bioactivity import (
    ExternalBioactivityRecord,
)


class BioactivitySource(Protocol):
    def fetch(
        self,
        *,
        target_id: str,
        activity_type: str,
    ) -> list[ExternalBioactivityRecord]: ...
