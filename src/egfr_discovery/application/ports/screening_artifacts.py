from pathlib import Path
from typing import Protocol

from egfr_discovery.application.dto.external_bioactivity import (
    CurationResult,
    ExternalBioactivityRecord,
    RejectedBioactivityRecord,
)
from egfr_discovery.application.dto.screening import RankedCandidate


class ScreeningArtifacts(Protocol):
    def save_raw(
        self,
        records: list[ExternalBioactivityRecord],
        target_id: str,
    ) -> Path: ...

    def save_curation(self, result: CurationResult) -> tuple[Path, Path]: ...

    def save_curation_failure(
        self,
        dataset_id: str,
        rejected: tuple[RejectedBioactivityRecord, ...],
    ) -> Path: ...

    def save_ranked(
        self,
        candidates: list[RankedCandidate],
        destination: Path,
        disclaimer: str,
    ) -> Path: ...
