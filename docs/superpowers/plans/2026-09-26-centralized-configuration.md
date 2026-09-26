# Centralized Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a typed, cached application settings module that validates the ChEMBL base URL and loads it from the environment or `.env`.

**Architecture:** `egfr_discovery.config` will be an infrastructure-level module built on `pydantic-settings`; domain and application code will remain independent of it. A cached factory will provide one validated settings object during normal execution while allowing tests to clear the cache.

**Tech Stack:** Python 3.14, Pydantic 2, pydantic-settings, pytest

---

## File Structure

- Create `src/egfr_discovery/config.py`: define the validated settings model and cached accessor.
- Create `tests/unit/test_config.py`: verify source precedence, URL validation, dotenv behavior, and caching.

### Task 1: Add tested centralized configuration

**Files:**
- Create: `src/egfr_discovery/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write the failing configuration tests**

Create `tests/unit/test_config.py`:

```python
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from egfr_discovery.config import Settings, get_settings


@pytest.fixture(autouse=True)
def isolate_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    get_settings.cache_clear()
    monkeypatch.delenv("CHEMBL_CLIENT_BASE_URL", raising=False)
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

    assert str(settings.chembl_client_base_url) == (
        "https://chembl.example.test/api"
    )


def test_environment_overrides_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "CHEMBL_CLIENT_BASE_URL=https://dotenv.example.test/api\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "CHEMBL_CLIENT_BASE_URL", "https://environment.example.test/api"
    )

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
    monkeypatch.setenv(
        "CHEMBL_CLIENT_BASE_URL", "https://cached.example.test/api"
    )

    first = get_settings()
    second = get_settings()

    assert first is second
```

- [ ] **Step 2: Run the tests and verify the missing module causes failure**

Run:

```bash
uv run pytest tests/unit/test_config.py -v
```

Expected: test collection fails with `ModuleNotFoundError: No module named 'egfr_discovery.config'`.

- [ ] **Step 3: Implement the minimal settings module**

Create `src/egfr_discovery/config.py`:

```python
from functools import cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    chembl_client_base_url: HttpUrl = HttpUrl(
        "https://www.ebi.ac.uk/chembl/api/data"
    )


@cache
def get_settings() -> Settings:
    """Return the process-wide validated application configuration."""
    return Settings()
```

- [ ] **Step 4: Run the focused tests and verify they pass**

Run:

```bash
uv run pytest tests/unit/test_config.py -v
```

Expected: all five configuration tests pass.

- [ ] **Step 5: Run focused formatting and static checks**

Run:

```bash
uv run ruff format --check src/egfr_discovery/config.py tests/unit/test_config.py
uv run ruff check src/egfr_discovery/config.py tests/unit/test_config.py
uv run mypy src/egfr_discovery/config.py
```

Expected: all commands exit successfully with no findings.

- [ ] **Step 6: Run repository verification**

Run:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
uv run lint-imports
git diff --check
git diff -- src/egfr_discovery/config.py tests/unit/test_config.py
```

Expected: the full test suite passes. Any pre-existing Ruff, mypy, or import-linter failures outside these two files are recorded accurately and left unchanged.

- [ ] **Step 7: Commit the implementation**

```bash
git add src/egfr_discovery/config.py tests/unit/test_config.py
git commit -m "Add centralized application configuration"
```
