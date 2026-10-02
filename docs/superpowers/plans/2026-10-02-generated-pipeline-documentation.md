# Generated Pipeline Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and verify a root-level `pipelines.md` that gives learners and practitioners accurate, extensible documentation for every registered end-to-end screening pipeline.

**Architecture:** Immutable Pydantic models represent pipelines and ordered sections. Pure application code renders Markdown, a filesystem adapter reads and writes it through an application port, bootstrap owns the registry and dependency construction, and a thin Typer command supports write and non-mutating check modes. Screening execution remains independent of documentation generation.

**Tech Stack:** Python 3.14, Pydantic 2, Typer, pytest, Ruff, mypy, import-linter

---

## File Structure

- Create `src/egfr_discovery/application/dto/pipeline_documentation.py`: validated section, pipeline, and registry models.
- Create `src/egfr_discovery/application/ports/pipeline_documentation_output.py`: read/write filesystem boundary.
- Create `src/egfr_discovery/application/use_cases/render_pipeline_documentation.py`: deterministic Markdown renderer.
- Create `src/egfr_discovery/application/use_cases/generate_pipeline_documentation.py`: write/check orchestration.
- Create `src/egfr_discovery/adapters/outbound/persistence/filesystem_pipeline_documentation.py`: UTF-8 output adapter.
- Create `src/egfr_discovery/bootstrap/pipeline_documentation.py`: current registry and dependency construction.
- Create `src/egfr_discovery/adapters/inbound/cli/pipeline_docs.py`: developer CLI.
- Modify `pyproject.toml`: register `egfr-pipeline-docs`.
- Create `pipelines.md`: generated documentation artifact.
- Add focused tests under `tests/unit/application`, `tests/unit/adapters`, `tests/unit/bootstrap`, and `tests/unit/cli`.

### Task 1: Add extensible, validated documentation metadata

**Files:**
- Create: `src/egfr_discovery/application/dto/pipeline_documentation.py`
- Create: `tests/unit/application/test_pipeline_documentation_models.py`

- [ ] **Step 1: Write failing metadata tests**

Create `tests/unit/application/test_pipeline_documentation_models.py`:

```python
import pytest
from pydantic import ValidationError

from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentation,
    PipelineDocumentationRegistry,
    PipelineDocumentationSection,
    REQUIRED_PIPELINE_SECTION_KEYS,
)


def required_sections() -> tuple[PipelineDocumentationSection, ...]:
    return tuple(
        PipelineDocumentationSection(
            key=key,
            heading=key.replace("_", " ").title(),
            body=f"Content for {key}.",
        )
        for key in REQUIRED_PIPELINE_SECTION_KEYS
    )


def pipeline(
    pipeline_id: str = "screening",
    sections: tuple[PipelineDocumentationSection, ...] | None = None,
) -> PipelineDocumentation:
    return PipelineDocumentation(
        pipeline_id=pipeline_id,
        title="Screening pipeline",
        summary="A short pipeline summary.",
        sections=sections or required_sections(),
    )


@pytest.mark.parametrize("field", ["key", "heading", "body"])
def test_section_rejects_blank_text(field: str) -> None:
    values = {"key": "inputs", "heading": "Inputs", "body": "Body"}
    values[field] = "   "
    with pytest.raises(ValidationError):
        PipelineDocumentationSection(**values)


def test_pipeline_requires_all_sections_and_learner_summary_first() -> None:
    with pytest.raises(ValidationError, match="drug_discovery_value"):
        pipeline(sections=required_sections()[:-1])

    sections = required_sections()
    with pytest.raises(ValidationError, match="plain_language_summary"):
        pipeline(sections=(sections[1], sections[0], *sections[2:]))


def test_pipeline_rejects_duplicate_section_keys() -> None:
    duplicate = PipelineDocumentationSection(
        key="inputs", heading="Other inputs", body="Other content."
    )
    with pytest.raises(ValidationError, match="Duplicate section key"):
        pipeline(sections=(*required_sections(), duplicate))


def test_registry_rejects_duplicate_pipeline_ids() -> None:
    with pytest.raises(ValidationError, match="Duplicate pipeline id"):
        PipelineDocumentationRegistry(pipelines=(pipeline(), pipeline()))


def test_additional_section_is_supported_in_declared_order() -> None:
    extra = PipelineDocumentationSection(
        key="limitations", heading="Limitations", body="Known limitations."
    )
    documented = pipeline(sections=(*required_sections(), extra))
    assert documented.sections[-1] == extra
```

- [ ] **Step 2: Run the tests and verify the missing-module failure**

Run: `uv run pytest tests/unit/application/test_pipeline_documentation_models.py -v`

Expected: collection fails because `pipeline_documentation` does not exist.

- [ ] **Step 3: Implement immutable metadata models**

Create `src/egfr_discovery/application/dto/pipeline_documentation.py`:

```python
from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

REQUIRED_PIPELINE_SECTION_KEYS = (
    "plain_language_summary",
    "inputs",
    "prediction_and_features",
    "models_and_rationale",
    "drug_discovery_use",
    "drug_discovery_value",
)


class PipelineDocumentationSection(BaseModel):
    model_config = ConfigDict(frozen=True)
    key: str
    heading: str
    body: str

    @field_validator("key", "heading", "body", mode="before")
    @classmethod
    def reject_blank_text(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Pipeline documentation text cannot be blank")
        return value.strip()


class PipelineDocumentation(BaseModel):
    model_config = ConfigDict(frozen=True)
    pipeline_id: str
    title: str
    summary: str
    sections: tuple[PipelineDocumentationSection, ...]

    @field_validator("pipeline_id", "title", "summary", mode="before")
    @classmethod
    def reject_blank_text(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Pipeline documentation text cannot be blank")
        return value.strip()

    @model_validator(mode="after")
    def validate_sections(self) -> Self:
        keys = [section.key for section in self.sections]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate section key")
        missing = [
            key for key in REQUIRED_PIPELINE_SECTION_KEYS if key not in keys
        ]
        if missing:
            raise ValueError(f"Missing required sections: {', '.join(missing)}")
        if keys[0] != "plain_language_summary":
            raise ValueError("plain_language_summary must be the first section")
        return self


class PipelineDocumentationRegistry(BaseModel):
    model_config = ConfigDict(frozen=True)
    pipelines: tuple[PipelineDocumentation, ...]

    @model_validator(mode="after")
    def reject_duplicate_pipeline_ids(self) -> Self:
        ids = [pipeline.pipeline_id for pipeline in self.pipelines]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate pipeline id")
        return self
```

- [ ] **Step 4: Run focused verification**

```bash
uv run pytest tests/unit/application/test_pipeline_documentation_models.py -v
uv run ruff check src/egfr_discovery/application/dto/pipeline_documentation.py tests/unit/application/test_pipeline_documentation_models.py
uv run mypy src/egfr_discovery/application/dto/pipeline_documentation.py
```

Expected: all commands pass.

- [ ] **Step 5: Commit**

```bash
git add src/egfr_discovery/application/dto/pipeline_documentation.py tests/unit/application/test_pipeline_documentation_models.py
git commit -m "Add pipeline documentation metadata"
```

### Task 2: Render deterministic Markdown

**Files:**
- Create: `src/egfr_discovery/application/use_cases/render_pipeline_documentation.py`
- Create: `tests/unit/application/test_render_pipeline_documentation.py`

- [ ] **Step 1: Write failing renderer tests**

Create `tests/unit/application/test_render_pipeline_documentation.py`:

```python
from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentation,
    PipelineDocumentationRegistry,
    PipelineDocumentationSection,
    REQUIRED_PIPELINE_SECTION_KEYS,
)
from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    GENERATED_NOTICE,
    RESEARCH_DISCLAIMER,
    render_pipeline_documentation,
)


def registry_with_extra_section() -> PipelineDocumentationRegistry:
    sections = tuple(
        PipelineDocumentationSection(
            key=key,
            heading=key.replace("_", " ").title(),
            body=f"Body for {key}.",
        )
        for key in REQUIRED_PIPELINE_SECTION_KEYS
    )
    extra = PipelineDocumentationSection(
        key="limitations", heading="Limitations", body="Known limits."
    )
    return PipelineDocumentationRegistry(
        pipelines=(
            PipelineDocumentation(
                pipeline_id="screening",
                title="Screening Pipeline",
                summary="Summary.",
                sections=(*sections, extra),
            ),
        )
    )


def test_render_is_deterministic_and_has_one_trailing_newline() -> None:
    registry = registry_with_extra_section()

    first = render_pipeline_documentation(registry)
    second = render_pipeline_documentation(registry)

    assert first == second
    assert first.endswith("\n") and not first.endswith("\n\n")
    assert GENERATED_NOTICE in first
    assert RESEARCH_DISCLAIMER in first
    assert first.index("### Plain Language Summary") < first.index("### Inputs")
    assert first.index("### Inputs") < first.index("### Limitations")
```

- [ ] **Step 2: Run the test and verify the missing-renderer failure**

Run: `uv run pytest tests/unit/application/test_render_pipeline_documentation.py -v`

Expected: collection fails because the renderer does not exist.

- [ ] **Step 3: Implement the pure renderer**

Create `src/egfr_discovery/application/use_cases/render_pipeline_documentation.py`:

```python
from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentationRegistry,
)

GENERATED_NOTICE = (
    "<!-- Generated by `uv run egfr-pipeline-docs`; do not edit directly. -->"
)
RESEARCH_DISCLAIMER = (
    "These pipelines produce research predictions for prioritization. "
    "Their outputs are not experimentally validated medicines or clinical "
    "recommendations."
)


def render_pipeline_documentation(
    registry: PipelineDocumentationRegistry,
) -> str:
    lines = [
        GENERATED_NOTICE,
        "",
        "# Screening Pipelines",
        "",
        "This document explains the repository's end-to-end screening pipelines.",
        "",
        f"> **Research-use notice:** {RESEARCH_DISCLAIMER}",
    ]
    for documented in registry.pipelines:
        lines.extend(("", f"## {documented.title}", "", documented.summary))
        for section in documented.sections:
            lines.extend(("", f"### {section.heading}", "", section.body))
    return "\n".join(lines).rstrip() + "\n"
```

- [ ] **Step 4: Run focused verification**

```bash
uv run pytest tests/unit/application/test_render_pipeline_documentation.py -v
uv run ruff check src/egfr_discovery/application/use_cases/render_pipeline_documentation.py tests/unit/application/test_render_pipeline_documentation.py
uv run mypy src/egfr_discovery/application/use_cases/render_pipeline_documentation.py
```

Expected: all commands pass.

- [ ] **Step 5: Commit**

```bash
git add src/egfr_discovery/application/use_cases/render_pipeline_documentation.py tests/unit/application/test_render_pipeline_documentation.py
git commit -m "Render pipeline documentation"
```

### Task 3: Add write and non-mutating check modes

**Files:**
- Create: `src/egfr_discovery/application/ports/pipeline_documentation_output.py`
- Create: `src/egfr_discovery/application/use_cases/generate_pipeline_documentation.py`
- Create: `src/egfr_discovery/adapters/outbound/persistence/filesystem_pipeline_documentation.py`
- Create: `tests/unit/application/test_generate_pipeline_documentation.py`
- Create: `tests/unit/adapters/test_filesystem_pipeline_documentation.py`

- [ ] **Step 1: Write failing generation tests**

Create `tests/unit/application/test_generate_pipeline_documentation.py`:

```python
from pathlib import Path

import pytest

from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentation,
    PipelineDocumentationRegistry,
    PipelineDocumentationSection,
    REQUIRED_PIPELINE_SECTION_KEYS,
)
from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentation,
    GeneratePipelineDocumentationCommand,
    PipelineDocumentationMissing,
    PipelineDocumentationStale,
)


@pytest.fixture
def registry() -> PipelineDocumentationRegistry:
    sections = tuple(
        PipelineDocumentationSection(
            key=key,
            heading=key.replace("_", " ").title(),
            body=f"Body for {key}.",
        )
        for key in REQUIRED_PIPELINE_SECTION_KEYS
    )
    return PipelineDocumentationRegistry(
        pipelines=(
            PipelineDocumentation(
                pipeline_id="screening",
                title="Screening Pipeline",
                summary="Summary.",
                sections=sections,
            ),
        )
    )


class InMemoryOutput:
    def __init__(self, content: str | None = None) -> None:
        self.content = content
        self.writes = 0

    def read(self, destination: Path) -> str | None:
        return self.content

    def write(self, destination: Path, content: str) -> None:
        self.content = content
        self.writes += 1


def test_write_mode_creates_document(
    registry: PipelineDocumentationRegistry,
) -> None:
    output = InMemoryOutput()
    result = GeneratePipelineDocumentation(registry, output).execute(
        GeneratePipelineDocumentationCommand()
    )
    assert output.writes == 1
    assert output.content is not None
    assert result.changed and not result.checked


def test_check_mode_accepts_current_content_without_writing(
    registry: PipelineDocumentationRegistry,
) -> None:
    output = InMemoryOutput()
    use_case = GeneratePipelineDocumentation(registry, output)
    use_case.execute(GeneratePipelineDocumentationCommand())
    output.writes = 0

    result = use_case.execute(GeneratePipelineDocumentationCommand(check=True))

    assert result.checked and not result.changed
    assert output.writes == 0


def test_check_mode_distinguishes_missing_and_stale(
    registry: PipelineDocumentationRegistry,
) -> None:
    missing = InMemoryOutput()
    stale = InMemoryOutput("stale\n")
    with pytest.raises(PipelineDocumentationMissing):
        GeneratePipelineDocumentation(registry, missing).execute(
            GeneratePipelineDocumentationCommand(check=True)
        )
    with pytest.raises(PipelineDocumentationStale):
        GeneratePipelineDocumentation(registry, stale).execute(
            GeneratePipelineDocumentationCommand(check=True)
        )
    assert missing.writes == 0
    assert stale.content == "stale\n"
    assert stale.writes == 0
```

- [ ] **Step 2: Write the failing filesystem-adapter test**

Create `tests/unit/adapters/test_filesystem_pipeline_documentation.py`:

```python
from pathlib import Path

from egfr_discovery.adapters.outbound.persistence.filesystem_pipeline_documentation import (
    FilesystemPipelineDocumentationOutput,
)


def test_output_reads_missing_as_none_and_round_trips_utf8(tmp_path: Path) -> None:
    output = FilesystemPipelineDocumentationOutput()
    destination = tmp_path / "nested" / "pipelines.md"
    assert output.read(destination) is None

    output.write(destination, "pIC50 prioritization — research only\n")

    assert output.read(destination) == "pIC50 prioritization — research only\n"
```

- [ ] **Step 3: Run tests and verify missing-module failures**

```bash
uv run pytest tests/unit/application/test_generate_pipeline_documentation.py tests/unit/adapters/test_filesystem_pipeline_documentation.py -v
```

Expected: collection fails for the missing use case and adapter.

- [ ] **Step 4: Define the output port**

Create `src/egfr_discovery/application/ports/pipeline_documentation_output.py`:

```python
from pathlib import Path
from typing import Protocol


class PipelineDocumentationOutput(Protocol):
    def read(self, destination: Path) -> str | None: ...

    def write(self, destination: Path, content: str) -> None: ...
```

- [ ] **Step 5: Implement generation behavior**

Create `src/egfr_discovery/application/use_cases/generate_pipeline_documentation.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentationRegistry,
)
from egfr_discovery.application.ports.pipeline_documentation_output import (
    PipelineDocumentationOutput,
)
from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
)


class GeneratePipelineDocumentationCommand(BaseModel):
    destination: Path = Path("pipelines.md")
    check: bool = False


@dataclass(frozen=True, slots=True)
class GeneratePipelineDocumentationResult:
    destination: Path
    checked: bool
    changed: bool


class PipelineDocumentationMissing(RuntimeError):
    pass


class PipelineDocumentationStale(RuntimeError):
    pass


class GeneratePipelineDocumentation:
    def __init__(
        self,
        registry: PipelineDocumentationRegistry,
        output: PipelineDocumentationOutput,
    ) -> None:
        self._registry = registry
        self._output = output

    def execute(
        self, command: GeneratePipelineDocumentationCommand
    ) -> GeneratePipelineDocumentationResult:
        expected = render_pipeline_documentation(self._registry)
        current = self._output.read(command.destination)
        if command.check:
            if current is None:
                raise PipelineDocumentationMissing(
                    f"Pipeline documentation is missing: {command.destination}"
                )
            if current != expected:
                raise PipelineDocumentationStale(
                    f"Pipeline documentation is stale: {command.destination}"
                )
            return GeneratePipelineDocumentationResult(
                destination=command.destination, checked=True, changed=False
            )

        changed = current != expected
        if changed:
            self._output.write(command.destination, expected)
        return GeneratePipelineDocumentationResult(
            destination=command.destination, checked=False, changed=changed
        )
```

- [ ] **Step 6: Implement the filesystem adapter**

Create `src/egfr_discovery/adapters/outbound/persistence/filesystem_pipeline_documentation.py`:

```python
from pathlib import Path


class FilesystemPipelineDocumentationOutput:
    def read(self, destination: Path) -> str | None:
        if not destination.is_file():
            return None
        return destination.read_text(encoding="utf-8")

    def write(self, destination: Path, content: str) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
```

- [ ] **Step 7: Run focused verification**

```bash
uv run pytest tests/unit/application/test_generate_pipeline_documentation.py tests/unit/adapters/test_filesystem_pipeline_documentation.py -v
uv run ruff check src/egfr_discovery/application/ports/pipeline_documentation_output.py src/egfr_discovery/application/use_cases/generate_pipeline_documentation.py src/egfr_discovery/adapters/outbound/persistence/filesystem_pipeline_documentation.py tests/unit/application/test_generate_pipeline_documentation.py tests/unit/adapters/test_filesystem_pipeline_documentation.py
uv run mypy src/egfr_discovery/application/ports/pipeline_documentation_output.py src/egfr_discovery/application/use_cases/generate_pipeline_documentation.py src/egfr_discovery/adapters/outbound/persistence/filesystem_pipeline_documentation.py
```

Expected: all commands pass.

- [ ] **Step 8: Commit**

```bash
git add src/egfr_discovery/application/ports/pipeline_documentation_output.py src/egfr_discovery/application/use_cases/generate_pipeline_documentation.py src/egfr_discovery/adapters/outbound/persistence/filesystem_pipeline_documentation.py tests/unit/application/test_generate_pipeline_documentation.py tests/unit/adapters/test_filesystem_pipeline_documentation.py
git commit -m "Add pipeline documentation generation"
```

### Task 4: Register the EGFR pipeline and add the CLI

**Files:**
- Create: `src/egfr_discovery/bootstrap/pipeline_documentation.py`
- Create: `src/egfr_discovery/adapters/inbound/cli/pipeline_docs.py`
- Modify: `pyproject.toml`
- Create: `tests/unit/bootstrap/test_pipeline_documentation.py`
- Create: `tests/unit/cli/test_pipeline_docs.py`

- [ ] **Step 1: Write failing registry-content tests**

Create `tests/unit/bootstrap/test_pipeline_documentation.py`:

```python
from egfr_discovery.bootstrap.pipeline_documentation import (
    PIPELINE_DOCUMENTATION_REGISTRY,
)


def test_egfr_screening_documentation_matches_the_implemented_science() -> None:
    documented = PIPELINE_DOCUMENTATION_REGISTRY.pipelines[0]
    sections = {section.key: section.body for section in documented.sections}
    all_content = "\n".join(sections.values())

    assert documented.pipeline_id == "egfr_screening"
    assert "laboratory testing is costly" in sections["plain_language_summary"]
    assert "prioritization" in sections["plain_language_summary"]
    assert "compound_id" in sections["inputs"]
    assert "smiles" in sections["inputs"]
    assert "pIC50" in sections["prediction_and_features"]
    assert "TF-IDF" in sections["prediction_and_features"]
    assert "one through three" in sections["prediction_and_features"]
    assert "RandomForestRegressor" in sections["models_and_rationale"]
    assert "standard deviation" in sections["models_and_rationale"]
    assert "descriptor" in sections["drug_discovery_use"]
    assert "diversity" in sections["drug_discovery_use"]
    assert "experimental" in sections["drug_discovery_value"]
    assert "clinical recommendation" in all_content
```

- [ ] **Step 2: Write failing CLI tests**

Create `tests/unit/cli/test_pipeline_docs.py`:

```python
from pathlib import Path

import pytest
from typer.testing import CliRunner

from egfr_discovery.adapters.inbound.cli.pipeline_docs import app


def test_cli_writes_and_checks_root_document(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    written = runner.invoke(app, [])
    checked = runner.invoke(app, ["--check"])

    assert written.exit_code == 0, written.output
    assert (tmp_path / "pipelines.md").is_file()
    assert "Wrote pipelines.md" in written.output
    assert checked.exit_code == 0, checked.output
    assert "pipelines.md is current" in checked.output


def test_cli_check_does_not_modify_missing_or_stale_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    missing = runner.invoke(app, ["--check"])
    assert missing.exit_code == 1
    assert not (tmp_path / "pipelines.md").exists()

    (tmp_path / "pipelines.md").write_text("stale\n", encoding="utf-8")
    stale = runner.invoke(app, ["--check"])
    assert stale.exit_code == 1
    assert (tmp_path / "pipelines.md").read_text(encoding="utf-8") == "stale\n"
    assert "run `uv run egfr-pipeline-docs`" in stale.output.lower()
```

- [ ] **Step 3: Run tests and verify missing registry/CLI failures**

Run: `uv run pytest tests/unit/bootstrap/test_pipeline_documentation.py tests/unit/cli/test_pipeline_docs.py -v`

Expected: collection fails because the registry and CLI do not exist.

- [ ] **Step 4: Create the registry and bootstrap functions**

Create `src/egfr_discovery/bootstrap/pipeline_documentation.py`:

```python
from egfr_discovery.adapters.outbound.persistence.filesystem_pipeline_documentation import (
    FilesystemPipelineDocumentationOutput,
)
from egfr_discovery.application.dto.pipeline_documentation import (
    PipelineDocumentation,
    PipelineDocumentationRegistry,
    PipelineDocumentationSection,
)
from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentation,
    GeneratePipelineDocumentationCommand,
    GeneratePipelineDocumentationResult,
)

PIPELINE_DOCUMENTATION_REGISTRY = PipelineDocumentationRegistry(
    pipelines=(
        PipelineDocumentation(
            pipeline_id="egfr_screening",
            title="EGFR Small-Molecule Screening Pipeline",
            summary=(
                "This pipeline prioritizes small molecules that may inhibit EGFR "
                "for research follow-up."
            ),
            sections=(
                PipelineDocumentationSection(
                    key="plain_language_summary",
                    heading="Plain-Language Summary",
                    body=(
                        "EGFR is a protein whose altered forms can help some cancers "
                        "grow. This pipeline learns patterns from previous laboratory "
                        "measurements of compounds tested against EGFR. It estimates "
                        "which compounds in a new list may be more active, removes "
                        "candidates with unfavorable basic properties, avoids returning "
                        "many nearly identical compounds, and creates a shortlist for "
                        "laboratory follow-up. This is useful because laboratory testing "
                        "is costly and slow, so computational prioritization helps "
                        "researchers decide what to test first. The shortlist is a set "
                        "of research hypotheses, not proof that any compound works."
                    ),
                ),
                PipelineDocumentationSection(
                    key="inputs",
                    heading="Input Summary",
                    body=(
                        "Model development starts from ChEMBL EGFR IC50 measurements. "
                        "The pipeline retains exact, positive IC50 values reported in "
                        "nM, validates structures, records rejected data with reasons, "
                        "and separates training and validation records by compound. "
                        "Screening input is a caller-provided CSV with `compound_id` "
                        "and `smiles` columns. SMILES is a text notation for molecular "
                        "structure."
                    ),
                ),
                PipelineDocumentationSection(
                    key="prediction_and_features",
                    heading="Prediction Target and Features",
                    body=(
                        "The model predicts continuous pIC50, a logarithmic expression "
                        "of IC50 in molar units where a larger value represents a lower "
                        "predicted concentration for 50% inhibition. Features are "
                        "character-level TF-IDF n-grams of lengths one through three "
                        "derived from each SMILES string. They do not represent measured "
                        "binding, a three-dimensional binding pose, safety, or clinical "
                        "efficacy."
                    ),
                ),
                PipelineDocumentationSection(
                    key="models_and_rationale",
                    heading="Models and Rationale",
                    body=(
                        "The activity model is a deterministic `RandomForestRegressor`. "
                        "A nonlinear tree ensemble can learn interactions in the sparse "
                        "SMILES-derived representation without assuming a linear "
                        "response. The population standard deviation across individual "
                        "tree predictions is reported as model-dispersion uncertainty; "
                        "it is not calibrated experimental uncertainty."
                    ),
                ),
                PipelineDocumentationSection(
                    key="drug_discovery_use",
                    heading="How Predictions Are Used in Drug Discovery",
                    body=(
                        "Predicted pIC50 is combined with deterministic molecular "
                        "descriptors and explicit property filters. Morgan-fingerprint "
                        "similarity then supports diversity selection so the shortlist "
                        "does not contain only close structural analogues. A ranking "
                        "step combines predicted potency, properties, and model "
                        "dispersion to prioritize compounds for expert review and "
                        "experimental testing."
                    ),
                ),
                PipelineDocumentationSection(
                    key="drug_discovery_value",
                    heading="Why This Information Is Useful",
                    body=(
                        "Computational prioritization can reduce a large library to a "
                        "smaller and more chemically varied set of hypotheses, making "
                        "experimental resources easier to focus. Predicted pIC50 and "
                        "model dispersion support relative comparison, but they do not "
                        "establish potency, selectivity, safety, developability, or "
                        "clinical utility and must not be used as a clinical "
                        "recommendation."
                    ),
                ),
            ),
        ),
    )
)


def build_pipeline_documentation_generator() -> GeneratePipelineDocumentation:
    return GeneratePipelineDocumentation(
        PIPELINE_DOCUMENTATION_REGISTRY,
        FilesystemPipelineDocumentationOutput(),
    )


def run_pipeline_documentation(
    command: GeneratePipelineDocumentationCommand,
) -> GeneratePipelineDocumentationResult:
    return build_pipeline_documentation_generator().execute(command)
```

- [ ] **Step 5: Implement the Typer CLI**

Create `src/egfr_discovery/adapters/inbound/cli/pipeline_docs.py`:

```python
from typing import Annotated

import typer

from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentationCommand,
    PipelineDocumentationMissing,
    PipelineDocumentationStale,
)
from egfr_discovery.bootstrap.pipeline_documentation import run_pipeline_documentation

app = typer.Typer(add_completion=False)


@app.command()
def generate(check: Annotated[bool, typer.Option("--check")] = False) -> None:
    try:
        result = run_pipeline_documentation(
            GeneratePipelineDocumentationCommand(check=check)
        )
    except (PipelineDocumentationMissing, PipelineDocumentationStale) as error:
        typer.echo(str(error), err=True)
        typer.echo("Run `uv run egfr-pipeline-docs` to regenerate it.", err=True)
        raise typer.Exit(code=1) from error

    if result.checked:
        typer.echo(f"{result.destination} is current")
    elif result.changed:
        typer.echo(f"Wrote {result.destination}")
    else:
        typer.echo(f"{result.destination} is already current")


def main() -> None:
    app()
```

- [ ] **Step 6: Register the command without adding dependencies**

Add to `[project.scripts]` in `pyproject.toml`:

```toml
egfr-pipeline-docs = "egfr_discovery.adapters.inbound.cli.pipeline_docs:main"
```

Pydantic and Typer already exist in project dependencies, so do not modify the dependency list or `uv.lock`.

- [ ] **Step 7: Run focused verification**

```bash
uv run pytest tests/unit/bootstrap/test_pipeline_documentation.py tests/unit/cli/test_pipeline_docs.py -v
uv run egfr-pipeline-docs --help
uv run ruff check src/egfr_discovery/bootstrap/pipeline_documentation.py src/egfr_discovery/adapters/inbound/cli/pipeline_docs.py tests/unit/bootstrap/test_pipeline_documentation.py tests/unit/cli/test_pipeline_docs.py
uv run mypy src/egfr_discovery/bootstrap/pipeline_documentation.py src/egfr_discovery/adapters/inbound/cli/pipeline_docs.py
```

Expected: tests and static checks pass; help lists `--check`.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/egfr_discovery/bootstrap/pipeline_documentation.py src/egfr_discovery/adapters/inbound/cli/pipeline_docs.py tests/unit/bootstrap/test_pipeline_documentation.py tests/unit/cli/test_pipeline_docs.py
git commit -m "Add pipeline documentation command"
```

### Task 5: Generate and lock the committed `pipelines.md`

**Files:**
- Create: `pipelines.md`
- Create: `tests/unit/test_pipelines_markdown.py`

- [ ] **Step 1: Write the synchronization test before generating the file**

Create `tests/unit/test_pipelines_markdown.py`:

```python
from pathlib import Path

from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
)
from egfr_discovery.bootstrap.pipeline_documentation import (
    PIPELINE_DOCUMENTATION_REGISTRY,
)


def test_committed_pipeline_documentation_matches_registry() -> None:
    repository_root = Path(__file__).parents[2]
    committed = (repository_root / "pipelines.md").read_text(encoding="utf-8")
    assert committed == render_pipeline_documentation(
        PIPELINE_DOCUMENTATION_REGISTRY
    )
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `uv run pytest tests/unit/test_pipelines_markdown.py -v`

Expected: failure because root-level `pipelines.md` does not exist.

- [ ] **Step 3: Generate the committed document**

Run: `uv run egfr-pipeline-docs`

Expected: `Wrote pipelines.md` and a root-level document containing the six required sections.

- [ ] **Step 4: Verify synchronization and check mode**

```bash
uv run pytest tests/unit/test_pipelines_markdown.py -v
uv run egfr-pipeline-docs --check
```

Expected: the test passes and the command prints `pipelines.md is current`.

- [ ] **Step 5: Inspect the generated scientific language**

Confirm in `pipelines.md` that:

- The learner summary appears first and explains what happens and why it helps.
- EGFR, IC50/pIC50, and SMILES are explained without overstating their meaning.
- Features match the implemented character TF-IDF n-gram range `(1, 3)`.
- The model matches `RandomForestRegressor` and uncertainty matches tree prediction standard deviation.
- Descriptor filtering, Morgan-fingerprint diversity, and ranking match the code.
- The research-only notice and experimental limitations are explicit.

- [ ] **Step 6: Commit**

```bash
git add pipelines.md tests/unit/test_pipelines_markdown.py
git commit -m "Generate screening pipeline documentation"
```

### Task 6: Full verification and handoff

**Files:**
- Review every file listed above.

- [ ] **Step 1: Format only feature files**

Run `uv run ruff format` with the exact Python source and test paths created in Tasks 1–5. Do not format unrelated repository files.

- [ ] **Step 2: Run the complete verification suite**

```bash
uv run pytest
uv run ruff check .
uv run mypy src
uv run lint-imports
uv run egfr-pipeline-docs --check
git diff --check
```

Expected: tests, type checks, architecture contracts, and documentation synchronization pass. If repository-wide Ruff reports pre-existing issues outside this feature, verify all changed files separately and report the exact unrelated failures without modifying those files.

- [ ] **Step 3: Verify generation is runtime-independent**

```bash
uv run python -c "from egfr_discovery.bootstrap.pipeline_documentation import PIPELINE_DOCUMENTATION_REGISTRY; print(len(PIPELINE_DOCUMENTATION_REGISTRY.pipelines))"
```

Expected: prints `1` without network access, model training, RDKit calculation, or screening artifacts.

- [ ] **Step 4: Review the final diff and generated-file hygiene**

```bash
git status --short
git diff --stat
git diff --check
```

Confirm that no `.env`, logs, model artifacts, datasets, caches, or unrelated files are staged.

- [ ] **Step 5: Commit verification-only formatting changes if present**

If formatting changed intended feature files, stage only those files and commit:

```bash
git add pipelines.md pyproject.toml src/egfr_discovery/application/dto/pipeline_documentation.py src/egfr_discovery/application/ports/pipeline_documentation_output.py src/egfr_discovery/application/use_cases/render_pipeline_documentation.py src/egfr_discovery/application/use_cases/generate_pipeline_documentation.py src/egfr_discovery/adapters/outbound/persistence/filesystem_pipeline_documentation.py src/egfr_discovery/bootstrap/pipeline_documentation.py src/egfr_discovery/adapters/inbound/cli/pipeline_docs.py tests/unit/application/test_pipeline_documentation_models.py tests/unit/application/test_render_pipeline_documentation.py tests/unit/application/test_generate_pipeline_documentation.py tests/unit/adapters/test_filesystem_pipeline_documentation.py tests/unit/bootstrap/test_pipeline_documentation.py tests/unit/cli/test_pipeline_docs.py tests/unit/test_pipelines_markdown.py
git commit -m "Finalize generated pipeline documentation"
```

If formatting made no changes, do not create an empty commit.
