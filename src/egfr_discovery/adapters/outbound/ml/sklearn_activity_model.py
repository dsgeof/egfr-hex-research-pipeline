from pathlib import Path
from typing import Sequence

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.prediction import ActivityPrediction

# Implementation of the ActivityModel protocol using scikit-learn.
# This model uses a TF-IDF vectorizer for feature extraction from SMILES strings
# and a logistic regression classifier for activity prediction.
class SklearnActivityModel:
    def __init__(self) -> None:
        # Initialize the vectorizer and classifier for the activity model.
        self._vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(1, 3))
        self._classifier = LogisticRegression(max_iter=1_000)
        self._trained = False

    # Train the activity model with the given compounds and labels.
    def train(self, compounds: Sequence[Compound], labels: Sequence[int]) -> None:
        if len(compounds) != len(labels):
            raise ValueError("The number of compounds must match the number of labels.")
        # Train the activity model using the provided compounds and labels.
        smiles = [compound.smiles for compound in compounds]
        # Transform the SMILES strings into feature vectors for the classifier.
        X = self._vectorizer.fit_transform(smiles)
        self._classifier.fit(X, labels)
        self._trained = True

    # Predict activity for the given compounds using the trained model.
    def predict(self, compounds: Sequence[Compound]) -> list[ActivityPrediction]:
        # Predict activity for the given compounds.
        if not self._trained:
            raise RuntimeError("Model has not been trained - training is required before prediction.")

        smiles = [compound.smiles for compound in compounds]
        # Transform the SMILES strings into feature vectors for the classifier.
        X = self._vectorizer.transform(smiles)
        # Predict the probabilities of activity for each compound (returns an array of probabilities)
        probabilities = self._classifier.predict_proba(X)[:, 1]
        # Create ActivityPrediction (domain/prediction.py) instances for each compound based on the predicted probabilities.
        predictions = [
            ActivityPrediction(compound=compound, predicted_probability=float(prob), uncertainty=abs(float(prob) - 0.5))
            for compound, prob in zip(compounds, probabilities, strict=True)
        ]
        return predictions


    # Persist the trained model to the specified destination.
    def save(self, destination: str) -> None:
        if not self._trained:
            raise RuntimeError("Model has not been trained - training is required before saving.")
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"vectorizer": self._vectorizer, "classifier": self._classifier}, destination)


   