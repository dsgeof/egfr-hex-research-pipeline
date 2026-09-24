
# ------------------------------------------------------------------------------------------------------- #
# Factory function to build and return a TrainActivityModel instance.                                     #
# This function encapsulates the creation of the activity model and its corresponding use case.           #
# ------------------------------------------------------------------------------------------------------- #
from egfr_discovery.adapters.outbound.ml.sklearn_activity_model import (
    SklearnActivityModel,
)
from egfr_discovery.application.use_cases.train_activity_model import (
    TrainActivityModel,
)

def build_train_activity_model() -> TrainActivityModel:
    model = SklearnActivityModel()
    return TrainActivityModel(model=model)



# ------------------------------------------------------------------------------------------------------- #
# Factory function to build and return a MolecularDescriptorCalculator instance.                          #
# This function encapsulates the creation of the RDKit descriptor calculator.                             #
# ------------------------------------------------------------------------------------------------------- #
from egfr_discovery.adapters.outbound.chemistry.rdkit_descriptors import (
    RDKitDescriptorCalculator,
)
from egfr_discovery.application.ports.molecular_descriptors import (
    MolecularDescriptorCalculator,
)

def build_molecular_descriptor_calculator() -> MolecularDescriptorCalculator:
    return RDKitDescriptorCalculator()


