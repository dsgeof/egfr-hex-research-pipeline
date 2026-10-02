from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from egfr_discovery.application.dto.pipeline_documentation import (
    REQUIRED_PIPELINE_SECTION_KEYS,
    PipelineDocumentation,
    PipelineDocumentationRegistry,
    PipelineDocumentationSection,
)
from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentation,
    GeneratePipelineDocumentationCommand,
    PipelineDocumentationMissing,
    PipelineDocumentationStale,
)
from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
)


@pytest.fixture
def registry() -> PipelineDocumentationRegistry:
    return PipelineDocumentationRegistry(
        pipelines=(
            PipelineDocumentation(
                pipeline_id="screening",
                title="Screening Pipeline",
                summary="Summary.",
                sections=tuple(
                    PipelineDocumentationSection(
                        key=key, heading=key.replace("_", " ").title(), body=f"{key}."
                    )
                    for key in REQUIRED_PIPELINE_SECTION_KEYS
                ),
            ),
        )
    )


class InMemoryOutput:
    def __init__(self, content: str | None = None) -> None:
        self.content = content
        self.reads: list[Path] = []
        self.writes: list[tuple[Path, str]] = []

    def read(self, destination: Path) -> str | None:
        self.reads.append(destination)
        return self.content

    def write(self, destination: Path, content: str) -> None:
        self.content = content
        self.writes.append((destination, content))


@pytest.mark.parametrize("current", [None, "stale\n"])
def test_write_mode_creates_or_updates_document(
    registry: PipelineDocumentationRegistry, current: str | None
) -> None:
    output = InMemoryOutput(current)

    result = GeneratePipelineDocumentation(registry, output).execute(
        GeneratePipelineDocumentationCommand()
    )

    expected = render_pipeline_documentation(registry)
    assert output.content == expected
    assert output.writes == [(Path("pipelines.md"), expected)]
    assert result.destination == Path("pipelines.md")
    assert result.changed and not result.checked


def test_unchanged_write_mode_does_not_rewrite(
    registry: PipelineDocumentationRegistry,
) -> None:
    output = InMemoryOutput(render_pipeline_documentation(registry))

    result = GeneratePipelineDocumentation(registry, output).execute(
        GeneratePipelineDocumentationCommand()
    )

    assert not result.changed and not result.checked
    assert output.writes == []


def test_check_mode_accepts_current_content_without_writing(
    registry: PipelineDocumentationRegistry,
) -> None:
    expected = render_pipeline_documentation(registry)
    output = InMemoryOutput(expected)

    result = GeneratePipelineDocumentation(registry, output).execute(
        GeneratePipelineDocumentationCommand(check=True)
    )

    assert result.checked and not result.changed
    assert output.content == expected
    assert output.writes == []


@pytest.mark.parametrize(
    ("current", "error"),
    [
        (None, PipelineDocumentationMissing),
        ("stale\n", PipelineDocumentationStale),
        ("", PipelineDocumentationStale),
    ],
)
def test_check_errors_do_not_mutate_output(
    registry: PipelineDocumentationRegistry,
    current: str | None,
    error: type[Exception],
) -> None:
    output = InMemoryOutput(current)
    destination = Path("custom/pipelines.md")

    with pytest.raises(error, match="custom/pipelines.md"):
        GeneratePipelineDocumentation(registry, output).execute(
            GeneratePipelineDocumentationCommand(destination=destination, check=True)
        )

    assert output.reads == [destination]
    assert output.content == current
    assert output.writes == []


@pytest.mark.parametrize("check", [False, True])
def test_destination_propagates_to_output_and_result(
    registry: PipelineDocumentationRegistry, check: bool
) -> None:
    expected = render_pipeline_documentation(registry)
    output = InMemoryOutput(expected if check else None)
    destination = Path("custom/pipelines.md")

    result = GeneratePipelineDocumentation(registry, output).execute(
        GeneratePipelineDocumentationCommand(destination=destination, check=check)
    )

    assert output.reads == [destination]
    assert output.writes == ([] if check else [(destination, expected)])
    assert result.destination == destination


def test_result_is_frozen_and_slotted(
    registry: PipelineDocumentationRegistry,
) -> None:
    result = GeneratePipelineDocumentation(registry, InMemoryOutput()).execute(
        GeneratePipelineDocumentationCommand()
    )

    with pytest.raises(FrozenInstanceError):
        result.changed = False  # type: ignore[misc]
    assert not hasattr(result, "__dict__")


def test_command_parses_destination_at_boundary() -> None:
    command = GeneratePipelineDocumentationCommand.model_validate(
        {"destination": "nested/pipelines.md"}
    )

    assert command.destination == Path("nested/pipelines.md")
    assert not command.check
