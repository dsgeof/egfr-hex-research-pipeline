from typing import Protocol


# Protocol for calculating molecular fingerprints and their similarity.
class MolecularFingerprintCalculator(Protocol):
    def fingerprint(self, smiles: str) -> object: ...

    # Calculates the similarity between two molecular fingerprints.
    def similarity(self, left: object, right: object) -> float: ...
