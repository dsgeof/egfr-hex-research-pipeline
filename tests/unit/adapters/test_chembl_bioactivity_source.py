from typing import Any

from egfr_discovery.adapters.outbound.chembl.bioactivity_source_data import (
    ChEMBLBioactivitySource,
)
from egfr_discovery.application.dto.external_bioactivity import (
    ExternalBioactivityRecord,
)


class StubChEMBLClient:
    def get_activities(self, **_: object) -> list[dict[str, Any]]:
        return [
            {
                "activity_id": 42,
                "molecule_chembl_id": "CHEMBL42",
                "target_chembl_id": "CHEMBL203",
                "assay_chembl_id": "CHEMBL-A42",
                "standard_type": "IC50",
                "standard_relation": "=",
                "standard_value": "12.5",
                "standard_units": "nM",
                "molecule_structures": {"canonical_smiles": "CCO"},
                "confidence_score": 9,
            }
        ]


def test_maps_chembl_payload_to_application_record() -> None:
    source = ChEMBLBioactivitySource(client=StubChEMBLClient())  # type: ignore[arg-type]

    records = source.fetch(target_id="CHEMBL203", activity_type="IC50")

    assert records == [
        ExternalBioactivityRecord(
            activity_id=42,
            compound_id="CHEMBL42",
            target_id="CHEMBL203",
            assay_id="CHEMBL-A42",
            activity_type="IC50",
            relation="=",
            value="12.5",
            units="nM",
            smiles="CCO",
            target_confidence=9,
            source="ChEMBL",
        )
    ]


def test_maps_activity_endpoint_top_level_canonical_smiles() -> None:
    class TopLevelSmilesClient:
        def get_activities(self, **_: object) -> list[dict[str, Any]]:
            return [
                {
                    "activity_id": 7,
                    "molecule_chembl_id": "CHEMBL7",
                    "canonical_smiles": "CCN",
                }
            ]

    source = ChEMBLBioactivitySource(client=TopLevelSmilesClient())  # type: ignore[arg-type]

    assert source.fetch(target_id="CHEMBL203", activity_type="IC50")[0].smiles == (
        "CCN"
    )


def test_missing_compound_identifier_is_preserved_for_curation_rejection() -> None:
    class MissingCompoundClient:
        def get_activities(self, **_: object) -> list[dict[str, Any]]:
            return [{"activity_id": 8, "canonical_smiles": "CCO"}]

    source = ChEMBLBioactivitySource(client=MissingCompoundClient())  # type: ignore[arg-type]

    assert source.fetch(target_id="CHEMBL203", activity_type="IC50")[0].compound_id == (
        ""
    )
