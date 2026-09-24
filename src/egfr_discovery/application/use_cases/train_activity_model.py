from dataclasses import dataclass
from typing import Sequence

from egfr_discovery.application.ports.activity_model import ActivityModel
from egfr_discovery.domain.compound import Compound

# Use case for training an activity prediction model.

@dataclass(frozen=True, slots=True)
class TrainingRecord:
    compound: Compound
    activity_label: int

@dataclass(frozen=True, slots=True)
class TrainActivityModelCommand:
    records: Sequence[TrainingRecord]
    model_destination: str


class TrainActivityModel:
    def __init__(self, model: ActivityModel) -> None:
        self._model = model

    # Execute the training process for the activity model using the provided command.
    def execute(self, command: TrainActivityModelCommand) -> None:

        if not command.records:
            raise ValueError("Training records cannot be empty")
        # Extract compounds and activity labels from the training records.
        compounds = [record.compound for record in command.records]
        labels = [record.activity_label for record in command.records]

        if len(set(labels)) < 2:
            raise ValueError("Training requires both active and inactive records")
        # Train the model with the extracted compounds and labels.
        self._model.train(compounds, labels)
        self._model.save(command.model_destination)