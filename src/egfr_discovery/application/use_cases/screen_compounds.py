from egfr_discovery.application.dto.screening import ScreeningLibrary
from egfr_discovery.application.ports.activity_model import ActivityModel
from egfr_discovery.domain.prediction import ActivityPrediction


class ScreenCompounds:
    def __init__(self, model: ActivityModel) -> None:
        self._model = model

    def execute(self, library: ScreeningLibrary) -> list[ActivityPrediction]:
        return self._model.predict(list(library.compounds))
