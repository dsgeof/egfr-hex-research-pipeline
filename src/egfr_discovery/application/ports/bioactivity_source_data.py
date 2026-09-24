from typing import Protocol

class BioactivitySource(Protocol):

    def get_activity_records(self, target_id: str) -> list[RawActivityRecord]:
        ...