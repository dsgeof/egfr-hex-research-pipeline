from dataclasses import dataclass
from random import Random

from egfr_discovery.domain.dataset import CuratedDataset


@dataclass(frozen=True, slots=True)
class DatasetSplit:
    train: CuratedDataset
    validation: CuratedDataset


class SplitBioactivityDataset:
    def __init__(
        self,
        validation_fraction: float = 0.2,
        random_seed: int = 42,
    ) -> None:
        if not 0 < validation_fraction < 1:
            raise ValueError("Validation fraction must be between 0 and 1")
        self._validation_fraction = validation_fraction
        self._random_seed = random_seed

    def execute(self, dataset: CuratedDataset) -> DatasetSplit:
        compound_ids = sorted(
            {measurement.compound_id for measurement in dataset.measurements}
        )
        if len(compound_ids) < 4:
            raise ValueError("Dataset must contain at least 4 unique compounds")

        Random(self._random_seed).shuffle(compound_ids)
        validation_count = max(
            2,
            round(len(compound_ids) * self._validation_fraction),
        )
        validation_count = min(validation_count, len(compound_ids) - 2)
        validation_ids = set(compound_ids[:validation_count])

        train_measurements = tuple(
            measurement
            for measurement in dataset.measurements
            if measurement.compound_id not in validation_ids
        )
        validation_measurements = tuple(
            measurement
            for measurement in dataset.measurements
            if measurement.compound_id in validation_ids
        )
        return DatasetSplit(
            train=CuratedDataset(
                dataset_id=f"{dataset.dataset_id}-train",
                measurements=train_measurements,
            ),
            validation=CuratedDataset(
                dataset_id=f"{dataset.dataset_id}-validation",
                measurements=validation_measurements,
            ),
        )
