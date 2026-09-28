from typing import Protocol


class MolecularStructureValidator(Protocol):
    """Validate a molecular structure representation."""

    def is_valid(self, smiles: str) -> bool: ...
