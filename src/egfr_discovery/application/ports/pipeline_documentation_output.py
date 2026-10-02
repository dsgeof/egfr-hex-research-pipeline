from pathlib import Path
from typing import Protocol


class PipelineDocumentationOutput(Protocol):
    def read(self, destination: Path) -> str | None: ...

    def write(self, destination: Path, content: str) -> None: ...
