from egfr_discovery.adapters.outbound.ml.sklearn_activity_model import (
    SklearnActivityModel,
)
from egfr_discovery.application.use_cases.train_activity_model import (
    TrainActivityModel,
)
# Factory function to build and return a TrainActivityModel instance.
# This function encapsulates the creation of the activity model and its corresponding use case.
def build_train_activity_model() -> TrainActivityModel:
    model = SklearnActivityModel()
    return TrainActivityModel(model=model)