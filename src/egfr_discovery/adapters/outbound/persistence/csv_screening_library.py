import csv
from pathlib import Path

from egfr_discovery.application.dto.screening import (
    ScreeningLibrary,
)
from egfr_discovery.domain.compound import Compound


class CsvScreeningLibrarySource:
    def load(self, path: str) -> ScreeningLibrary:
        source_path = Path(path)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        compounds: list[Compound] = []

        with source_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            required_headers = {"compound_id", "smiles"}
            if reader.fieldnames is None or not required_headers.issubset(
                reader.fieldnames
            ):
                raise ValueError("CSV must contain headers: compound_id, smiles")
            for row in reader:
                compounds.append(
                    Compound(
                        compound_id=row["compound_id"],
                        smiles=row["smiles"],
                    )
                )

        return ScreeningLibrary(
            library_id=source_path.stem,
            compounds=tuple(compounds),
            source_path=str(source_path),
        )
