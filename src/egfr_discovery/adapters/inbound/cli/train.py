from pathlib import Path

import pandas as pd

from egfr_discovery.application.use_cases.train_activity_model import (
    TrainActivityModelCommand,
    TrainingRecord,
)
from egfr_discovery.bootstrap.container import build_train_activity_model
from egfr_discovery.domain.compound import Compound

def train_from_csv(
    source: str = "data/raw/example_bioactivity.csv",
    destination: str = "artifacts/models/example_model.joblib",
) -> None:
    dataframe = pd.read_csv(source)

    records = [
        TrainingRecord(
            compound=Compound(
                compound_id=str(row.compound_id),
                smiles=str(row.smiles),
            ),
            activity_label=int(row.activity_label),
        )
        for row in dataframe.itertuples(index=False)
    ]

    command = TrainActivityModelCommand(
        records=records,
        model_destination=destination,
    )

    use_case = build_train_activity_model()
    use_case.execute(command)

    print(f"Saved model to {Path(destination).resolve()}")