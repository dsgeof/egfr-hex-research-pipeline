import pytest

from egfr_discovery.adapters.outbound.chemistry.rdkit_fingerprints import (
    RDKitFingerprintCalculator,
)


def test_fingerprint_similarity_is_one_for_identical_smiles() -> None:
    calculator = RDKitFingerprintCalculator()
    fingerprint = calculator.fingerprint("CCO")

    assert calculator.similarity(fingerprint, fingerprint) == pytest.approx(1.0)
    assert calculator.is_valid("CCO")


def test_fingerprint_rejects_invalid_smiles() -> None:
    calculator = RDKitFingerprintCalculator()

    with pytest.raises(ValueError, match="Invalid SMILES"):
        calculator.fingerprint("not-smiles")
    assert not calculator.is_valid("not-smiles")
