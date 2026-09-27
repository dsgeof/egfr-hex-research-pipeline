from dataclasses import dataclass

@dataclass
class RawDataActivityRecord:
    activity_id: str
    assay_id: str
    molecule_chembl_id: str
    canonical_smiles: str
    standard_type: str
    standard_value: float
    standard_units: str
    standard_relation: str