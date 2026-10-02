from pathlib import Path

from egfr_discovery.adapters.outbound.persistence.filesystem_pipeline_documentation import (
    FilesystemPipelineDocumentationOutput,
)


def test_read_missing_document_does_not_create_directories(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "pipelines.md"

    assert FilesystemPipelineDocumentationOutput().read(destination) is None
    assert not destination.parent.exists()


def test_read_directory_returns_none(tmp_path: Path) -> None:
    assert FilesystemPipelineDocumentationOutput().read(tmp_path) is None


def test_write_creates_parents_and_round_trips_utf8(tmp_path: Path) -> None:
    output = FilesystemPipelineDocumentationOutput()
    destination = tmp_path / "nested" / "docs" / "pipelines.md"
    content = "pIC50 prioritization — research only\n"

    output.write(destination, content)

    assert destination.read_bytes() == content.encode("utf-8")
    assert output.read(destination) == content


def test_write_replaces_existing_document(tmp_path: Path) -> None:
    destination = tmp_path / "pipelines.md"
    destination.write_text("stale text longer than replacement", encoding="utf-8")
    output = FilesystemPipelineDocumentationOutput()

    output.write(destination, "current\n")

    assert output.read(destination) == "current\n"
