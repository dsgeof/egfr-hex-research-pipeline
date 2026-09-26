import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from egfr_discovery.config import Settings, get_settings


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    get_settings.cache_clear()
    for name in tuple(os.environ):
        if name.casefold() == "chembl_client_base_url":
            monkeypatch.delenv(name)
    yield
    get_settings.cache_clear()


def test_uses_default_chembl_client_base_url() -> None:
    settings = Settings(_env_file=None)

    assert str(settings.chembl_client_base_url) == (
        "https://www.ebi.ac.uk/chembl/api/data"
    )


def test_loads_chembl_client_base_url_from_dotenv(tmp_path: Path) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "CHEMBL_CLIENT_BASE_URL=https://chembl.example.test/api\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=dotenv_path)

    assert str(settings.chembl_client_base_url) == ("https://chembl.example.test/api")


def test_environment_overrides_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "CHEMBL_CLIENT_BASE_URL=https://dotenv.example.test/api\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CHEMBL_CLIENT_BASE_URL", "https://environment.example.test/api")

    settings = Settings(_env_file=dotenv_path)

    assert str(settings.chembl_client_base_url) == (
        "https://environment.example.test/api"
    )


def test_rejects_invalid_chembl_client_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHEMBL_CLIENT_BASE_URL", "not-a-url")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_get_settings_returns_cached_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHEMBL_CLIENT_BASE_URL", "https://cached.example.test/api")

    first = get_settings()
    second = get_settings()

    assert first is second
