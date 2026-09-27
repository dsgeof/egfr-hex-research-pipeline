from typing import Any

from egfr_discovery.adapters.outbound.chembl.client import (
    ChEMBLClient,
)
from egfr_discovery.adapters.outbound.chembl.models import (
    ChEMBLActivityRecord,
)


class ChEMBLBioactivitySource:
    def __init__(self, client: ChEMBLClient) -> None:
        self._client = client

    def fetch(self, *, target_id: str, activity_type: str) -> list[ChEMBLActivityRecord]:
        """Fetch ChEMBL activity records for a given target and activity type.

        Args:
            target_id (str): The ChEMBL ID of the target.
            activity_type (str): The type of activity to fetch (e.g., "IC50").

        Returns:
            list[ChEMBLActivityRecord]: A list of ChEMBLActivityRecord instances.
        """
        raw_records = self._client.get_activities(
            target_chembl_id=target_id,
            standard_type=activity_type,
        )

        return [
            self._to_record(record)
            for record in raw_records
        ]

    def _to_record(self, raw: dict[str, Any]) -> ChEMBLActivityRecord:
        """Convert a raw ChEMBL activity record dictionary into a ChEMBLActivityRecord instance.
        Args:
            raw (dict[str, Any]): The raw ChEMBL activity record dictionary.

        Returns:
            ChEMBLActivityRecord: The converted ChEMBLActivityRecord instance.
        """
        molecule_structures = raw.get("molecule_structures") or {}

        return ChEMBLActivityRecord(
            activity_id=raw.get("activity_id"),
            molecule_chembl_id=raw["molecule_chembl_id"],
            target_chembl_id=raw.get("target_chembl_id"),
            assay_chembl_id=raw.get("assay_chembl_id"),

            standard_type=raw.get("standard_type"),
            standard_relation=raw.get("standard_relation"),
            standard_value=raw.get("standard_value"),
            standard_units=raw.get("standard_units"),

            canonical_smiles=molecule_structures.get(
                "canonical_smiles"
            ),

            target_pref_name=raw.get("target_pref_name"),
            target_organism=raw.get("target_organism"),

            assay_description=raw.get("assay_description"),
            pchembl_value=raw.get("pchembl_value"),
            confidence_score=raw.get("confidence_score"),
        )