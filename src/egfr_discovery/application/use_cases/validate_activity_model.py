from math import sqrt

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from egfr_discovery.application.dto.model_results import (
    ModelValidationResult,
    RegressionMetrics,
)
from egfr_discovery.application.ports.activity_model import ActivityModel
from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.dataset import CuratedDataset


class ValidateActivityModel:

    def __init__(self, model: ActivityModel, max_mae: float = 1.0) -> None:
        self._model = model
        self._max_mae = max_mae

    def execute(self, validation_dataset: CuratedDataset) -> ModelValidationResult:

        compounds = [
            Compound(
                compound_id=m.compound_id,
                smiles=m.smiles,
            )
            for m in validation_dataset.measurements
        ]

        expected = [
            m.pic50
            for m in validation_dataset.measurements
        ]

        predictions = self._model.predict(compounds)

        predicted = [
            p.predicted_pic50
            for p in predictions
        ]

        mae = mean_absolute_error(
            expected,
            predicted,
        )

        rmse = sqrt(
            mean_squared_error(
                expected,
                predicted,
            )
        )

        r2 = r2_score(
            expected,
            predicted,
        )

        failures: list[str] = []

        if mae > self._max_mae:
            failures.append(
                f"MAE {mae:.3f} exceeds "
                f"maximum {self._max_mae:.3f}"
            )

        return ModelValidationResult(
            passed=not failures,
            metrics=RegressionMetrics(
                mae=mae,
                rmse=rmse,
                r2=r2,
            ),
            failures=tuple(failures),
        )