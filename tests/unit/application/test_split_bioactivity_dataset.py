from decimal import Decimal

import pytest

from egfr_discovery.application.use_cases.split_bioactivity_dataset import (
    SplitBioactivityDataset,
)
from egfr_discovery.domain.bioactivity import BioactivityMeasurement
from egfr_discovery.domain.dataset import CuratedDataset


def dataset_with_repeated_compounds(unique_compounds: int) -> CuratedDataset:
    measurements: list[BioactivityMeasurement] = []
    activity_id = 1
    for index in range(unique_compounds):
        for repeat in range(2):
            measurements.append(
                BioactivityMeasurement(
                    activity_id=activity_id,
                    compound_id=f"CMP-{index}",
                    assay_id=f"ASSAY-{repeat}",
                    target_id="CHEMBL203",
                    smiles="C" * (index + 1),
                    ic50_nm=Decimal(str(10 + index + repeat)),
                )
            )
            activity_id += 1
    return CuratedDataset("dataset", tuple(measurements))


def test_split_is_deterministic_and_has_no_compound_overlap() -> None:
    dataset = dataset_with_repeated_compounds(unique_compounds=6)
    splitter = SplitBioactivityDataset(validation_fraction=0.33, random_seed=17)

    first = splitter.execute(dataset)
    second = splitter.execute(dataset)

    train_ids = {item.compound_id for item in first.train.measurements}
    validation_ids = {item.compound_id for item in first.validation.measurements}
    assert first == second
    assert train_ids.isdisjoint(validation_ids)
    assert len(train_ids) == 4
    assert len(validation_ids) == 2


def test_split_rejects_fewer_than_four_unique_compounds() -> None:
    with pytest.raises(ValueError, match="at least 4 unique compounds"):
        SplitBioactivityDataset().execute(dataset_with_repeated_compounds(3))
