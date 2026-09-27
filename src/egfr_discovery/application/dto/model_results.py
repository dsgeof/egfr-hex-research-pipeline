from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegressionMetrics:
    # Mean Absolute Error (Description: Average absolute difference between predicted and actual values)
    mae: float
    # Root Mean Squared Error (Description: Square root of the average squared differences between predicted and actual values)
    rmse: float
    # R-squared (Description: Proportion of variance in the dependent variable that is predictable from the independent variables)
    r2: float


@dataclass(frozen=True, slots=True)
class ModelValidationResult:
    passed: bool
    metrics: RegressionMetrics
    failures: tuple[str, ...]