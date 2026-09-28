from typing import Any

from egfr_discovery.adapters.outbound.chembl.client import ChEMBLClient
from egfr_discovery.application.dto.external_bioactivity import (
    ExternalBioactivityRecord,
)


class ChEMBLBioactivitySource:
    def __init__(self, client: ChEMBLClient) -> None:
        self._client = client

    def fetch(
        self,
        *,
        target_id: str,
        activity_type: str,
    ) -> list[ExternalBioactivityRecord]:
        raw_records = self._client.get_activities(
            target_chembl_id=target_id,
            standard_type=activity_type,
        )
        return [self._to_record(record) for record in raw_records]

    def _to_record(self, raw: dict[str, Any]) -> ExternalBioactivityRecord:
        molecule_structures = raw.get("molecule_structures") or {}
        return ExternalBioactivityRecord(
            activity_id=raw.get("activity_id"),
            compound_id=str(raw.get("molecule_chembl_id") or ""),
            target_id=raw.get("target_chembl_id"),
            assay_id=raw.get("assay_chembl_id"),
            activity_type=raw.get("standard_type"),
            relation=raw.get("standard_relation"),
            value=raw.get("standard_value"),
            units=raw.get("standard_units"),
            smiles=raw.get("canonical_smiles")
            or molecule_structures.get("canonical_smiles"),
            target_confidence=raw.get("confidence_score"),
            source="ChEMBL",
        )
