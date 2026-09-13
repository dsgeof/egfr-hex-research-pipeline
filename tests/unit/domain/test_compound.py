import pytest

from egfr_discovery.domain.compound import Compound, InvalidCompoundError


def test_compound_requires_an_id() -> None:
    with pytest.raises(InvalidCompoundError):
        Compound(compound_id="", smiles="CCO")


def test_compound_requires_smiles() -> None:
    with pytest.raises(InvalidCompoundError):
        Compound(compound_id="CMP-1", smiles="")


def test_valid_compound_is_created() -> None:
    compound = Compound(compound_id="CMP-1", smiles="CCO")

    assert compound.compound_id == "CMP-1"
    assert compound.smiles == "CCO"