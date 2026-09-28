from pathlib import Path

from egfr_discovery.adapters.outbound.ml.sklearn_activity_model import (
    SklearnActivityModel,
)
from egfr_discovery.application.use_cases.train_activity_model import (
    TrainActivityModel,
)


def build_train_activity_model(
    model_directory: Path = Path("artifacts/models"),
) -> TrainActivityModel:
    model = SklearnActivityModel()
    return TrainActivityModel(model=model, model_directory=model_directory)


from egfr_discovery.adapters.outbound.chemistry.rdkit_descriptors import (
    RDKitDescriptorCalculator,
)
from egfr_discovery.application.ports.molecular_descriptors import (
    MolecularDescriptorCalculator,
)


def build_molecular_descriptor_calculator() -> MolecularDescriptorCalculator:
    return RDKitDescriptorCalculator()
