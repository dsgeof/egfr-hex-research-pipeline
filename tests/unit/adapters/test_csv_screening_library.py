from pathlib import Path

import pytest

from egfr_discovery.adapters.outbound.persistence.csv_screening_library import (
    CsvScreeningLibrarySource,
)


def test_csv_source_requires_compound_id_and_smiles(tmp_path: Path) -> None:
    source = CsvScreeningLibrarySource()
    invalid = tmp_path / "library.csv"
    invalid.write_text("compound_id\nCMP-1\n", encoding="utf-8")

    with pytest.raises(ValueError, match="compound_id, smiles"):
        source.load(str(invalid))


def test_csv_source_preserves_compounds_and_source_path(tmp_path: Path) -> None:
    source_path = tmp_path / "library.csv"
    source_path.write_text(
        "compound_id,smiles\nCMP-1,CCO\nCMP-2,CCN\n",
        encoding="utf-8",
    )

    library = CsvScreeningLibrarySource().load(str(source_path))

    assert library.library_id == "library"
    assert library.source_path == str(source_path)
    assert [item.compound_id for item in library.compounds] == ["CMP-1", "CMP-2"]


def test_csv_source_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        CsvScreeningLibrarySource().load(str(tmp_path / "absent.csv"))
