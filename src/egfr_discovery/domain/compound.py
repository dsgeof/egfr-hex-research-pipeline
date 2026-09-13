from dataclasses import dataclass


class InvalidCompoundError(ValueError):
    """Raised when a compound has invalid identifying information."""


@dataclass(frozen=True, slots=True)
class Compound:
    compound_id: str
    smiles: str

    def __post_init__(self) -> None:
        if not self.compound_id.strip():
            raise InvalidCompoundError("compound_id cannot be empty")

        if not self.smiles.strip():
            raise InvalidCompoundError("smiles cannot be empty")