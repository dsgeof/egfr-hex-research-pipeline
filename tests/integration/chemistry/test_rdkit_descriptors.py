import pytest

from egfr_discovery.adapters.outbound.chemistry.rdkit_descriptors import (
    RDKitDescriptorCalculator,
)


def test_calculates_descriptors_for_valid_smiles() -> None:
    calculator = RDKitDescriptorCalculator()

    result = calculator.calculate("CCO")

    assert result.molecular_weight == pytest.approx(46.07, rel=0.01)
    assert result.hydrogen_bond_donors == 1
    assert result.hydrogen_bond_acceptors == 1
    assert result.polar_surface_area > 0


def test_rejects_invalid_smiles() -> None:
    calculator = RDKitDescriptorCalculator()

    with pytest.raises(ValueError, match="Invalid SMILES"):
        calculator.calculate("not-a-smiles")