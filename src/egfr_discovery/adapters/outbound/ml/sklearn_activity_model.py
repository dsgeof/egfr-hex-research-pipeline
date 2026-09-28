from pathlib import Path
from statistics import pstdev

import joblib  # type: ignore[import-untyped]
from sklearn.ensemble import RandomForestRegressor  # type: ignore[import-untyped]
from sklearn.feature_extraction.text import (  # type: ignore[import-untyped]
    TfidfVectorizer,
)

from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.prediction import ActivityPrediction


class SklearnActivityModel:
    def __init__(self, n_estimators: int = 64, random_seed: int = 42) -> None:
        self._vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 3))
        self._regressor = RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_seed,
            n_jobs=1,
        )
        self._trained = False

    def fit(self, compounds: list[Compound], labels: list[float]) -> None:
        if len(compounds) != len(labels):
            raise ValueError("The number of compounds and labels must match")
        if not compounds:
            raise ValueError("At least one compound is required for training")

        features = self._vectorizer.fit_transform(
            [compound.smiles for compound in compounds]
        )
        self._regressor.fit(features, labels)
        self._trained = True

    def predict(self, compounds: list[Compound]) -> list[ActivityPrediction]:
        self._require_trained()
        if not compounds:
            return []

        features = self._vectorizer.transform(
            [compound.smiles for compound in compounds]
        )
        values = self._regressor.predict(features)
        estimator_values = [
            estimator.predict(features) for estimator in self._regressor.estimators_
        ]
        return [
            ActivityPrediction(
                compound=compound,
                predicted_pic50=float(value),
                uncertainty=pstdev(
                    float(estimates[index]) for estimates in estimator_values
                ),
            )
            for index, (compound, value) in enumerate(
                zip(compounds, values, strict=True)
            )
        ]

    def save(self, destination: str) -> None:
        self._require_trained()
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"vectorizer": self._vectorizer, "regressor": self._regressor},
            path,
        )

    def _require_trained(self) -> None:
        if not self._trained:
            raise RuntimeError("Model has not been trained")
