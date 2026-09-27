from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors

from egfr_discovery.application.ports.molecular_descriptors import (
    MolecularDescriptors,
)


class RDKitDescriptorCalculator:
    def calculate(self, smiles: str) -> MolecularDescriptors:
        molecule = Chem.MolFromSmiles(smiles)

        if molecule is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        return MolecularDescriptors(
            molecular_weight=float(Descriptors.MolWt(molecule)),
            log_p=float(Crippen.MolLogP(molecule)),
            hydrogen_bond_donors=int(Lipinski.NumHDonors(molecule)),
            hydrogen_bond_acceptors=int(Lipinski.NumHAcceptors(molecule)),
            polar_surface_area=float(
                rdMolDescriptors.CalcTPSA(molecule)
            ),
        )


