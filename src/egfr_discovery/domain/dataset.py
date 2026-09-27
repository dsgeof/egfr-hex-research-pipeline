from dataclasses import dataclass

from egfr_discovery.domain.bioactivity import BioactivityMeasurement


@dataclass(frozen=True, slots=True)
class CuratedDataset:
    dataset_id: str
    measurements: tuple[BioactivityMeasurement, ...]

    def __post_init__(self) -> None:
        if not self.measurements:
            raise ValueError("Curated dataset cannot be empty")