from dataclasses import dataclass
from pathlib import Path

from egfr_discovery.application.ports.activity_model import ActivityModel
from egfr_discovery.domain.compound import Compound
from egfr_discovery.domain.dataset import CuratedDataset


@dataclass(frozen=True, slots=True)
class TrainModelResult:
    model_id: str
    training_size: int
    model_path: str


class TrainActivityModel:
    def __init__(
        self,
        model: ActivityModel,
        model_directory: Path = Path("artifacts/models"),
    ) -> None:
        self._model = model
        self._model_directory = model_directory

    def execute(self, dataset: CuratedDataset) -> TrainModelResult:

        compounds = [
            Compound(
                compound_id=m.compound_id,
                smiles=m.smiles,
            )
            for m in dataset.measurements
        ]

        labels = [m.pic50 for m in dataset.measurements]

        self._model.fit(
            compounds,
            labels,
        )

        model_path = self._model_directory / f"{dataset.dataset_id}.joblib"

        self._model.save(str(model_path))

        return TrainModelResult(
            model_id=f"{dataset.dataset_id}-model",
            training_size=len(compounds),
            model_path=str(model_path),
        )
