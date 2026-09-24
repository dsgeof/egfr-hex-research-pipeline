from dataclasses import dataclass
from typing import Protocol


# Dataclass representing molecular descriptors for a compound.
@dataclass(frozen=True, slots=True)
class MolecularDescriptors:
    molecular_weight: float
    log_p: float
    hydrogen_bond_donors: int
    hydrogen_bond_acceptors: int
    polar_surface_area: float


# Protocol defining the interface for a molecular descriptor calculator.
class MolecularDescriptorCalculator(Protocol):
    def calculate(self, smiles: str) -> MolecularDescriptors:
        ...

