from dataclasses import dataclass
from decimal import Decimal
from math import log10

@dataclass(frozen=True, slots=True)
class BioactivityMeasurement:
    activity_id: int
    compound_id: str
    assay_id: str

    target_id: str
    smiles: str
    ic50_nm: Decimal
    source: str = "ChEMBL"

    @property
    def ic50_molar(self) -> Decimal:
        return self.ic50_nm * Decimal("1e-9")

    @property
    def pIC50(self) -> float:
        return -log10(float(self.ic50_molar))