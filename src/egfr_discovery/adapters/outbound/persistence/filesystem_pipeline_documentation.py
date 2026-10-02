from pathlib import Path


class FilesystemPipelineDocumentationOutput:
    def read(self, destination: Path) -> str | None:
        if not destination.is_file():
            return None
        return destination.read_text(encoding="utf-8")

    def write(self, destination: Path, content: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
