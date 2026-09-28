from math import sqrt

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
            Compound(compound_id=item.compound_id, smiles=item.smiles)
            for item in validation_dataset.measurements
        ]
        expected = [item.pic50 for item in validation_dataset.measurements]
        predicted = [item.predicted_pic50 for item in self._model.predict(compounds)]
        if len(expected) != len(predicted):
            raise ValueError("Model returned an unexpected number of predictions")

        errors = [
            actual - prediction
            for actual, prediction in zip(expected, predicted, strict=True)
        ]
        mae = sum(abs(error) for error in errors) / len(errors)
        rmse = sqrt(sum(error**2 for error in errors) / len(errors))
        expected_mean = sum(expected) / len(expected)
        total_variance = sum((value - expected_mean) ** 2 for value in expected)
        residual_variance = sum(error**2 for error in errors)
        r2 = 0.0 if total_variance == 0 else 1 - residual_variance / total_variance

        failures = (
            (f"MAE {mae:.3f} exceeds maximum {self._max_mae:.3f}",)
            if mae > self._max_mae
            else ()
        )
        return ModelValidationResult(
            passed=not failures,
            metrics=RegressionMetrics(mae=mae, rmse=rmse, r2=r2),
            failures=failures,
        )
