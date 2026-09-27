from pydantic import BaseModel


class ChEMBLActivityRecord(BaseModel):
    activity_id: int | None = None
    molecule_chembl_id: str
    target_chembl_id: str | None = None
    assay_chembl_id: str | None = None
    standard_type: str | None = None
    standard_relation: str | None = None
    standard_value: str | float | None = None
    standard_units: str | None = None
    canonical_smiles: str | None = None
    target_pref_name: str | None = None
    target_organism: str | None = None
    assay_description: str | None = None
    pchembl_value: str | float | None = None
    confidence_score: int | None = None