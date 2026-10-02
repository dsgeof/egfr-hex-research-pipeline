from pathlib import Path


class FilesystemPipelineDocumentationOutput:
    def read(self, destination: Path) -> str | None:
        if not destination.is_file():
            return None
        with destination.open(encoding="utf-8", newline="") as handle:
            return handle.read()

    def write(self, destination: Path, content: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
