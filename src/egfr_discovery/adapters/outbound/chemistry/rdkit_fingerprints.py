from typing import cast

from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit.DataStructs.cDataStructs import ExplicitBitVect


class RDKitFingerprintCalculator:
    def __init__(self, radius: int = 2, fingerprint_size: int = 2_048) -> None:
        self._generator = rdFingerprintGenerator.GetMorganGenerator(
            radius=radius,
            fpSize=fingerprint_size,
        )

    def fingerprint(self, smiles: str) -> object:
        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise ValueError(f"Invalid SMILES: {smiles}")
        return self._generator.GetFingerprint(molecule)

    def similarity(self, left: object, right: object) -> float:
        return float(
            DataStructs.TanimotoSimilarity(
                cast(ExplicitBitVect, left),
                cast(ExplicitBitVect, right),
            )
        )

    def is_valid(self, smiles: str) -> bool:
        return Chem.MolFromSmiles(smiles) is not None
