from typing import Protocol

from egfr_discovery.application.dto.screening import (
    ScreeningLibrary,
)


class ScreeningLibrarySource(Protocol):
    def load(self, path: str) -> ScreeningLibrary: ...
