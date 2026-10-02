from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentationRegistry,
)
from egfr_discovery.application.ports.pipeline_documentation_output import (
    PipelineDocumentationOutput,
)
from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
)


class GeneratePipelineDocumentationCommand(BaseModel):
    destination: Path = Path("pipelines.md")
    check: bool = False


@dataclass(frozen=True, slots=True)
class GeneratePipelineDocumentationResult:
    destination: Path
    checked: bool
    changed: bool


class PipelineDocumentationMissing(Exception):
    """The requested documentation file does not exist."""


class PipelineDocumentationStale(Exception):
    """The documentation differs from the registered pipeline descriptions."""


class GeneratePipelineDocumentation:
    def __init__(
        self,
        registry: PipelineDocumentationRegistry,
        output: PipelineDocumentationOutput,
    ) -> None:
        self._registry = registry
        self._output = output

    def execute(
        self, command: GeneratePipelineDocumentationCommand
    ) -> GeneratePipelineDocumentationResult:
        expected = render_pipeline_documentation(self._registry)
        current = self._output.read(command.destination)
        if command.check:
            if current is None:
                raise PipelineDocumentationMissing(
                    f"Pipeline documentation is missing: {command.destination}"
                )
            if current != expected:
                raise PipelineDocumentationStale(
                    f"Pipeline documentation is stale: {command.destination}"
                )
            return GeneratePipelineDocumentationResult(
                destination=command.destination, checked=True, changed=False
            )

        changed = current != expected
        if changed:
            self._output.write(command.destination, expected)
        return GeneratePipelineDocumentationResult(
            destination=command.destination, checked=False, changed=changed
        )
