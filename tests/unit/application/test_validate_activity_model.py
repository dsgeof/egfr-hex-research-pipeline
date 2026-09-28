from decimal import Decimal

import pytest

from egfr_discovery.application.use_cases.validate_activity_model import (
    ValidateActivityModel,
)
from egfr_discovery.domain.bioactivity import BioactivityMeasurement
from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.dataset import CuratedDataset
from egfr_discovery.domain.prediction import ActivityPrediction


class StubActivityModel:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def fit(self, compounds: list[Compound], labels: list[float]) -> None:
        raise NotImplementedError

    def predict(self, compounds: list[Compound]) -> list[ActivityPrediction]:
        return [
            ActivityPrediction(compound, value, uncertainty=0.1)
            for compound, value in zip(compounds, self._values, strict=True)
        ]

    def save(self, destination: str) -> None:
        raise NotImplementedError


def validation_dataset() -> CuratedDataset:
    return CuratedDataset(
        "validation",
        tuple(
            BioactivityMeasurement(
                activity_id=index,
                compound_id=f"CMP-{index}",
                assay_id="ASSAY-1",
                target_id="CHEMBL203",
                smiles="C" * index,
                ic50_nm=Decimal(value),
            )
            for index, value in enumerate((100, 10, 1), start=1)
        ),
    )


def test_validation_calculates_regression_metrics() -> None:
    result = ValidateActivityModel(
        StubActivityModel([7.0, 7.5, 8.5]),
        max_mae=1.0,
    ).execute(validation_dataset())

    assert result.passed
    assert result.metrics.mae == pytest.approx(1 / 3)
    assert result.metrics.rmse == pytest.approx((0.5 / 3) ** 0.5)
    assert result.metrics.r2 == pytest.approx(0.75)
    assert result.failures == ()


def test_validation_reports_mae_threshold_failure() -> None:
    result = ValidateActivityModel(
        StubActivityModel([5.0, 5.0, 5.0]),
        max_mae=1.0,
    ).execute(validation_dataset())

    assert not result.passed
    assert result.failures == ("MAE 3.000 exceeds maximum 1.000",)
