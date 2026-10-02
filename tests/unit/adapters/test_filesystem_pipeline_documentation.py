from pathlib import Path

import pytest

from egfr_discovery.adapters.outbound.persistence.filesystem_pipeline_documentation import (
    FilesystemPipelineDocumentationOutput,
)
from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentationRegistry,
)
from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentation,
    GeneratePipelineDocumentationCommand,
    PipelineDocumentationStale,
)
from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
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


@pytest.mark.parametrize("newline", ["\r\n", "\r"])
def test_read_preserves_original_line_endings(tmp_path: Path, newline: str) -> None:
    destination = tmp_path / "pipelines.md"
    content = f"first{newline}second{newline}"
    destination.write_bytes(content.encode("utf-8"))

    assert FilesystemPipelineDocumentationOutput().read(destination) == content


@pytest.mark.parametrize("newline", ["\r\n", "\r"])
def test_check_rejects_non_lf_bytes_without_mutation(
    tmp_path: Path, newline: str
) -> None:
    registry = PipelineDocumentationRegistry(pipelines=())
    destination = tmp_path / "pipelines.md"
    original = render_pipeline_documentation(registry).replace("\n", newline).encode()
    destination.write_bytes(original)
    use_case = GeneratePipelineDocumentation(
        registry, FilesystemPipelineDocumentationOutput()
    )

    with pytest.raises(PipelineDocumentationStale):
        use_case.execute(
            GeneratePipelineDocumentationCommand(destination=destination, check=True)
        )

    assert destination.read_bytes() == original


@pytest.mark.parametrize("newline", ["\r\n", "\r"])
def test_write_corrects_non_lf_bytes_to_exact_rendered_bytes(
    tmp_path: Path, newline: str
) -> None:
    registry = PipelineDocumentationRegistry(pipelines=())
    expected = render_pipeline_documentation(registry)
    destination = tmp_path / "pipelines.md"
    destination.write_bytes(expected.replace("\n", newline).encode("utf-8"))

    result = GeneratePipelineDocumentation(
        registry, FilesystemPipelineDocumentationOutput()
    ).execute(GeneratePipelineDocumentationCommand(destination=destination))

    assert result.changed and not result.checked
    assert destination.read_bytes() == expected.encode("utf-8")
