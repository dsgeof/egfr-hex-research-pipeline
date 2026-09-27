from __future__ import annotations
from typing import Any
import httpx

from egfr_discovery.config import get_settings



class ChEMBLClient:
    BASE_URL = get_settings().chembl_client_base_url

    def __init__(
        self,
        timeout: float = 30.0,
    ) -> None:
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "egfr-discovery/0.1",
            },
        )

    def close(self) -> None:
        self._client.close()

    def get_activities(
        self,
        *,
        target_chembl_id: str,
        standard_type: str,
        page_size: int = 1000,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []

        offset = 0

        while True:
            response = self._client.get(
                f"{self.BASE_URL}/activity.json",
                params={
                    "target_chembl_id": target_chembl_id,
                    "standard_type": standard_type,
                    "limit": page_size,
                    "offset": offset,
                },
            )

            response.raise_for_status()
            payload = response.json()
            activities = payload.get("activities", [])

            if not activities:
                break

            records.extend(activities)
            page_meta = payload.get("page_meta", {})
            next_url = page_meta.get("next")

            if not next_url:
                break

            offset += page_size

        return records