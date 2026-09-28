from decimal import Decimal

import pytest

from egfr_discovery.application.dto.external_bioactivity import (
    ExternalBioactivityRecord,
)
from egfr_discovery.application.use_cases.curate_bioactivity_dataset import (
    CurateBioactivityCommand,
    CurateBioactivityDataset,
    NoAcceptedBioactivityRecords,
)


class StubStructureValidator:
    def __init__(self, valid_smiles: set[str]) -> None:
        self._valid_smiles = valid_smiles

    def is_valid(self, smiles: str) -> bool:
        return smiles in self._valid_smiles


def external_record(
    *,
    activity_id: int | None = 1,
    compound_id: str = "CHEMBL1",
    target_id: str | None = "CHEMBL203",
    assay_id: str | None = "CHEMBL-A1",
    activity_type: str | None = "IC50",
    relation: str | None = "=",
    value: str | float | None = "100",
    units: str | None = "nM",
    smiles: str | None = "CCO",
) -> ExternalBioactivityRecord:
    return ExternalBioactivityRecord(
        activity_id=activity_id,
        compound_id=compound_id,
        target_id=target_id,
        assay_id=assay_id,
        activity_type=activity_type,
        relation=relation,
        value=value,
        units=units,
        smiles=smiles,
        target_confidence=9,
    )


def test_curates_valid_record_and_reports_invalid_smiles() -> None:
    use_case = CurateBioactivityDataset(StubStructureValidator({"CCO"}))
    command = CurateBioactivityCommand(
        dataset_id="egfr-ic50-v1",
        records=[
            external_record(),
            external_record(activity_id=2, compound_id="CHEMBL2", smiles="bad"),
        ],
    )

    result = use_case.execute(command)

    assert len(result.dataset.measurements) == 1
    assert result.dataset.measurements[0].ic50_nm == Decimal(100)
    assert result.dataset.measurements[0].pic50 == pytest.approx(7.0)
    assert [item.reason for item in result.rejected] == ["invalid_smiles"]
    assert len(result.dataset.measurements) + len(result.rejected) == 2


@pytest.mark.parametrize(
    ("record", "reason"),
    [
        (external_record(activity_id=None), "missing_activity_id"),
        (external_record(assay_id=None), "missing_assay_id"),
        (external_record(assay_id="  "), "missing_assay_id"),
        (external_record(target_id=None), "missing_target_id"),
        (external_record(target_id=""), "missing_target_id"),
        (external_record(activity_type="Ki"), "wrong_activity_type"),
        (external_record(relation=">"), "non_exact_relation"),
        (external_record(units="uM"), "wrong_units"),
        (external_record(value=None), "missing_value"),
        (external_record(value="invalid"), "invalid_value"),
        (external_record(value="0"), "non_positive_value"),
        (external_record(smiles=None), "missing_smiles"),
        (external_record(smiles="CCO.CN"), "mixture"),
    ],
)
def test_reports_rejection_reason(
    record: ExternalBioactivityRecord,
    reason: str,
) -> None:
    use_case = CurateBioactivityDataset(StubStructureValidator({"CCO"}))

    result = use_case.execute(
        CurateBioactivityCommand(
            dataset_id="dataset",
            records=[external_record(activity_id=999), record],
        )
    )

    assert result.rejected[0].reason == reason


def test_all_rejected_records_are_attached_to_failure() -> None:
    use_case = CurateBioactivityDataset(StubStructureValidator({"CCO"}))

    with pytest.raises(NoAcceptedBioactivityRecords) as raised:
        use_case.execute(
            CurateBioactivityCommand(
                dataset_id="dataset",
                records=[external_record(smiles="invalid")],
            )
        )

    assert raised.value.dataset_id == "dataset"
    assert [item.reason for item in raised.value.rejected] == ["invalid_smiles"]
