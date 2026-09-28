import csv
from decimal import Decimal
from pathlib import Path

from egfr_discovery.bootstrap.container import build_train_activity_model
from egfr_discovery.domain.bioactivity import BioactivityMeasurement
from egfr_discovery.domain.dataset import CuratedDataset


def train_from_csv(
    source: str = "data/processed/egfr_training.csv",
    destination: str = "artifacts/models/example_model.joblib",
) -> None:
    destination_path = Path(destination)
    measurements: list[BioactivityMeasurement] = []
    with Path(source).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "activity_id",
            "compound_id",
            "assay_id",
            "target_id",
            "smiles",
            "ic50_nm",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(
                "Training CSV must contain activity_id, compound_id, assay_id, "
                "target_id, smiles, ic50_nm"
            )
        for row in reader:
            measurements.append(
                BioactivityMeasurement(
                    activity_id=int(row["activity_id"]),
                    compound_id=row["compound_id"],
                    assay_id=row["assay_id"],
                    target_id=row["target_id"],
                    smiles=row["smiles"],
                    ic50_nm=Decimal(row["ic50_nm"]),
                    source=row.get("source") or "ChEMBL",
                )
            )

    dataset = CuratedDataset(destination_path.stem, tuple(measurements))
    use_case = build_train_activity_model(destination_path.parent)
    result = use_case.execute(dataset)
    print(f"Saved model to {Path(result.model_path).resolve()}")
