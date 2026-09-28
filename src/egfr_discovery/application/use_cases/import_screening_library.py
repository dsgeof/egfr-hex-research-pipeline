from egfr_discovery.application.dto.screening import ScreeningLibrary
from egfr_discovery.application.ports.screening_library_source import (
    ScreeningLibrarySource,
)


class ImportScreeningLibrary:
    def __init__(self, source: ScreeningLibrarySource) -> None:
        self._source = source

    def execute(self, path: str) -> ScreeningLibrary:
        return self._source.load(path)
