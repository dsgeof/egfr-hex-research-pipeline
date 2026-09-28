from pathlib import Path

import pytest

from egfr_discovery.adapters.outbound.ml.sklearn_activity_model import (
    SklearnActivityModel,
)
from egfr_discovery.domain.compound import Compound


def compounds() -> list[Compound]:
    return [
        Compound("CMP-1", "CC"),
        Compound("CMP-2", "CCC"),
        Compound("CMP-3", "CCCC"),
        Compound("CMP-4", "c1ccccc1"),
    ]


def test_model_fits_predicts_pic50_and_saves(tmp_path: Path) -> None:
    model = SklearnActivityModel(n_estimators=8, random_seed=7)
    training_compounds = compounds()

    model.fit(training_compounds, [5.1, 5.8, 6.4, 7.2])
    predictions = model.predict(training_compounds)
    destination = tmp_path / "model.joblib"
    model.save(str(destination))

    assert len(predictions) == len(training_compounds)
    assert all(prediction.compound in training_compounds for prediction in predictions)
    assert all(0 < prediction.predicted_pic50 < 14 for prediction in predictions)
    assert all(
        prediction.uncertainty is not None and prediction.uncertainty >= 0
        for prediction in predictions
    )
    assert destination.is_file()


def test_model_rejects_mismatched_training_lengths() -> None:
    with pytest.raises(ValueError, match="must match"):
        SklearnActivityModel().fit(compounds(), [5.0])


def test_model_must_be_trained_before_prediction_or_save(tmp_path: Path) -> None:
    model = SklearnActivityModel()

    with pytest.raises(RuntimeError, match="trained"):
        model.predict(compounds())
    with pytest.raises(RuntimeError, match="trained"):
        model.save(str(tmp_path / "model.joblib"))
