# Executable Screening Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an executable, hexagonally wired EGFR screening command that fetches and curates ChEMBL data, trains and validates a pIC50 regressor, screens a caller-supplied library, and exports a provenance-preserving ranked result.

**Architecture:** Application-owned DTOs and ports define every external boundary. A single application orchestrator coordinates deterministic Python services; concrete ChEMBL, RDKit, sklearn, CSV, and filesystem adapters are constructed only in bootstrap. A Typer CLI builds a validated Pydantic command and reports research-only predictions.

**Tech Stack:** Python 3.14, Pydantic 2, Typer, HTTPX, RDKit, scikit-learn, joblib, pytest

---

## File Structure

- Modify `src/egfr_discovery/application/dto/external_bioactivity.py`: application-owned source record and curation result types.
- Modify `src/egfr_discovery/application/dto/screening.py`: validated pipeline command and typed screening/result records.
- Modify `src/egfr_discovery/application/ports/bioactivity_source_data.py`: return application DTOs.
- Create `src/egfr_discovery/application/ports/molecular_structure.py`: abstract SMILES validation.
- Create `src/egfr_discovery/application/ports/screening_artifacts.py`: abstract snapshot/report/result persistence.
- Modify `src/egfr_discovery/application/ports/activity_model.py`: consistent pIC50 model protocol.
- Modify `src/egfr_discovery/application/use_cases/curate_bioactivity_dataset.py`: explicit acceptance and rejection accounting.
- Modify `src/egfr_discovery/application/use_cases/ingest_bioactivity_data.py`: consume application DTOs and the structure-validation port.
- Create `src/egfr_discovery/application/use_cases/split_bioactivity_dataset.py`: deterministic compound-group split.
- Modify `src/egfr_discovery/application/use_cases/train_activity_model.py`: remove misplaced split DTO and train on `pic50`.
- Modify `src/egfr_discovery/application/use_cases/validate_activity_model.py`: standard-library regression metrics.
- Modify `src/egfr_discovery/application/use_cases/calculate_compound_properties.py`: typed evaluated candidates.
- Modify `src/egfr_discovery/application/use_cases/filter_candidates.py`: typed configurable filters.
- Modify `src/egfr_discovery/application/use_cases/select_diverse_candidates.py`: typed diversity selection.
- Modify `src/egfr_discovery/application/use_cases/rank_candidates.py`: retain complete candidate evidence.
- Create `src/egfr_discovery/application/use_cases/run_screening_pipeline.py`: end-to-end orchestration.
- Modify `src/egfr_discovery/domain/bioactivity.py`: canonical `pic50` property.
- Modify `src/egfr_discovery/domain/prediction.py`: pIC50 prediction contract.
- Modify `src/egfr_discovery/adapters/outbound/chembl/bioactivity_source_data.py`: map ChEMBL records to application DTOs.
- Modify `src/egfr_discovery/adapters/outbound/chembl/client.py`: injectable URL and context-managed cleanup.
- Modify `src/egfr_discovery/adapters/outbound/ml/sklearn_activity_model.py`: regression implementation and uncertainty.
- Modify `src/egfr_discovery/adapters/outbound/chemistry/rdkit_fingerprints.py`: fingerprint, similarity, and structure validation.
- Modify `src/egfr_discovery/adapters/outbound/persistence/csv_screening_library.py`: strict CSV validation and provenance.
- Create `src/egfr_discovery/adapters/outbound/persistence/filesystem_screening_artifacts.py`: artifact persistence.
- Replace `src/egfr_discovery/bootstrap/screening_pipeline.py`: dependency construction and `run_pipeline`.
- Modify `src/egfr_discovery/bootstrap/ingest.py`: preserve the existing ingestion command with aligned dependencies.
- Create `src/egfr_discovery/bootstrap/logging.py`: timestamped file and console logging.
- Create `src/egfr_discovery/adapters/inbound/cli/screen.py`: Typer command.
- Modify `pyproject.toml`: register `egfr-screen`.
- Modify `.gitignore`: ignore timestamped log files.
- Add focused tests under `tests/unit/` and `tests/integration/screening/`.

### Task 1: Align bioactivity contracts and preserve curation decisions

**Files:**
- Modify: `src/egfr_discovery/application/dto/external_bioactivity.py`
- Modify: `src/egfr_discovery/application/ports/bioactivity_source_data.py`
- Create: `src/egfr_discovery/application/ports/molecular_structure.py`
- Modify: `src/egfr_discovery/application/use_cases/curate_bioactivity_dataset.py`
- Modify: `src/egfr_discovery/application/use_cases/ingest_bioactivity_data.py`
- Modify: `src/egfr_discovery/domain/bioactivity.py`
- Modify: `src/egfr_discovery/adapters/outbound/chembl/bioactivity_source_data.py`
- Modify: `src/egfr_discovery/bootstrap/ingest.py`
- Test: `tests/unit/application/test_curate_bioactivity_dataset.py`
- Test: `tests/unit/adapters/test_chembl_bioactivity_source.py`

- [ ] **Step 1: Write failing tests for DTO mapping and explicit rejection reasons**

Tests must construct source-shaped records and assert that the ChEMBL adapter returns `ExternalBioactivityRecord`, accepted values retain their original identifiers and Decimal IC50 value, invalid structures are rejected with `invalid_smiles`, and every input appears exactly once in accepted or rejected output.

```python
def test_curates_valid_record_and_reports_invalid_smiles() -> None:
    validator = StubStructureValidator(valid_smiles={"CCO"})
    use_case = CurateBioactivityDataset(validator)
    command = CurateBioactivityCommand(
        dataset_id="egfr-ic50-v1",
        records=[valid_external_record(smiles="CCO"), valid_external_record(smiles="bad")],
    )

    result = use_case.execute(command)

    assert len(result.dataset.measurements) == 1
    assert result.dataset.measurements[0].pic50 == pytest.approx(7.0)
    assert [item.reason for item in result.rejected] == ["invalid_smiles"]
    assert len(result.dataset.measurements) + len(result.rejected) == 2
```

- [ ] **Step 2: Run the focused tests and confirm failures name the missing contracts**

Run: `uv run pytest tests/unit/application/test_curate_bioactivity_dataset.py tests/unit/adapters/test_chembl_bioactivity_source.py -v`

Expected: failures for missing `CurationResult`, `RejectedBioactivityRecord`, injected validator, and application-owned adapter output.

- [ ] **Step 3: Implement the application-owned contracts**

Use these exact public shapes:

```python
@dataclass(frozen=True, slots=True)
class ExternalBioactivityRecord:
    activity_id: int | None
    compound_id: str
    target_id: str | None
    assay_id: str | None
    activity_type: str | None
    relation: str | None
    value: str | float | None
    units: str | None
    smiles: str | None
    target_confidence: int | None
    source: str = "ChEMBL"


@dataclass(frozen=True, slots=True)
class RejectedBioactivityRecord:
    record: ExternalBioactivityRecord
    reason: str


@dataclass(frozen=True, slots=True)
class CurationResult:
    dataset: CuratedDataset
    rejected: tuple[RejectedBioactivityRecord, ...]
```

`BioactivitySource.fetch()` returns `list[ExternalBioactivityRecord]`. `MolecularStructureValidator.is_valid(smiles)` is a protocol method. `CurateBioactivityDataset` receives that validator, validates identifiers, activity type, equality relation, nM units, positive Decimal value, single-component valid SMILES, and returns the typed result. Add lowercase `BioactivityMeasurement.pic50`; keep `pIC50` as a compatibility alias returning `pic50`.

Refactor `IngestBioactivityDataset` to consume the same application DTO fields and injected structure validator, serialize dataclasses with `asdict`, and preserve its existing file/result interface. Update `bootstrap/ingest.py` to inject the RDKit implementation so the existing ingestion CLI remains functional.

- [ ] **Step 4: Run focused tests and static checks**

Run:

```bash
uv run pytest tests/unit/application/test_curate_bioactivity_dataset.py tests/unit/adapters/test_chembl_bioactivity_source.py -v
uv run ruff check src/egfr_discovery/application/dto/external_bioactivity.py src/egfr_discovery/application/ports/bioactivity_source_data.py src/egfr_discovery/application/ports/molecular_structure.py src/egfr_discovery/application/use_cases/curate_bioactivity_dataset.py src/egfr_discovery/application/use_cases/ingest_bioactivity_data.py src/egfr_discovery/domain/bioactivity.py src/egfr_discovery/adapters/outbound/chembl/bioactivity_source_data.py src/egfr_discovery/bootstrap/ingest.py
```

Expected: all focused tests and Ruff checks pass.

### Task 2: Add deterministic, leakage-free splitting

**Files:**
- Create: `src/egfr_discovery/application/use_cases/split_bioactivity_dataset.py`
- Modify: `src/egfr_discovery/application/use_cases/train_activity_model.py`
- Test: `tests/unit/application/test_split_bioactivity_dataset.py`

- [ ] **Step 1: Write failing tests for deterministic compound grouping**

```python
def test_split_is_deterministic_and_has_no_compound_overlap() -> None:
    dataset = dataset_with_repeated_compounds(unique_compounds=6)
    splitter = SplitBioactivityDataset(validation_fraction=0.33, random_seed=17)

    first = splitter.execute(dataset)
    second = splitter.execute(dataset)

    train_ids = {item.compound_id for item in first.train.measurements}
    validation_ids = {item.compound_id for item in first.validation.measurements}
    assert first == second
    assert train_ids.isdisjoint(validation_ids)


def test_split_rejects_fewer_than_four_unique_compounds() -> None:
    with pytest.raises(ValueError, match="at least 4 unique compounds"):
        SplitBioactivityDataset().execute(dataset_with_repeated_compounds(3))
```

- [ ] **Step 2: Run the tests and verify they fail for the missing use case**

Run: `uv run pytest tests/unit/application/test_split_bioactivity_dataset.py -v`

Expected: import failure for `split_bioactivity_dataset`.

- [ ] **Step 3: Implement `DatasetSplit` and `SplitBioactivityDataset`**

Group all measurements by `compound_id`, sort group IDs before applying `random.Random(seed).shuffle`, allocate at least two unique compounds to validation and at least two to training, flatten groups without separating repeated compounds, and suffix dataset IDs with `-train` and `-validation`. Remove the unrelated `DatasetSplit` declaration from `train_activity_model.py`.

- [ ] **Step 4: Verify the split tests**

Run: `uv run pytest tests/unit/application/test_split_bioactivity_dataset.py -v`

Expected: deterministic and insufficient-data tests pass.

### Task 3: Make model and prediction contracts consistently regress pIC50

**Files:**
- Modify: `src/egfr_discovery/domain/prediction.py`
- Modify: `src/egfr_discovery/application/ports/activity_model.py`
- Modify: `src/egfr_discovery/adapters/outbound/ml/sklearn_activity_model.py`
- Modify: `src/egfr_discovery/application/use_cases/train_activity_model.py`
- Modify: `src/egfr_discovery/application/use_cases/validate_activity_model.py`
- Test: `tests/unit/adapters/test_sklearn_activity_model.py`
- Test: `tests/unit/application/test_validate_activity_model.py`

- [ ] **Step 1: Write failing regression-contract tests**

```python
def test_model_fits_and_predicts_pic50(tmp_path: Path) -> None:
    model = SklearnActivityModel(random_seed=7, estimator_count=16)
    compounds = compounds_for(["CCO", "CCN", "c1ccccc1", "CC(=O)O"])
    model.fit(compounds, [7.0, 6.7, 8.1, 6.2])

    predictions = model.predict(compounds[:2])
    destination = tmp_path / "model.joblib"
    model.save(str(destination))

    assert all(math.isfinite(item.predicted_pic50) for item in predictions)
    assert all(item.uncertainty is None or item.uncertainty >= 0 for item in predictions)
    assert destination.exists()


def test_predict_rejects_untrained_model() -> None:
    with pytest.raises(RuntimeError, match="not been trained"):
        SklearnActivityModel().predict([Compound("CMP-1", "CCO")])
```

Validation tests use a fake `ActivityModel` and assert MAE, RMSE, R-squared, and failure gating without importing sklearn.

- [ ] **Step 2: Run focused tests and confirm the probability/fit mismatch**

Run: `uv run pytest tests/unit/adapters/test_sklearn_activity_model.py tests/unit/application/test_validate_activity_model.py -v`

Expected: failures because `predicted_pic50` and a working `fit` implementation are absent.

- [ ] **Step 3: Implement the regression model and standard-library metrics**

`ActivityPrediction` exposes `compound`, finite `predicted_pic50`, and optional finite non-negative `uncertainty`. The port uses `fit(compounds: list[Compound], labels: list[float])`, `predict(...)`, and `save(...)`.

The adapter uses the existing character TF-IDF representation with a deterministic `RandomForestRegressor`. Mean tree output becomes predicted pIC50 and population standard deviation becomes uncertainty. The saved joblib payload includes the vectorizer and regressor. `ValidateActivityModel` calculates MAE, RMSE, and R-squared with `math` and `statistics`, with no sklearn import in application code.

- [ ] **Step 4: Run focused model tests, Ruff, and mypy**

Run:

```bash
uv run pytest tests/unit/adapters/test_sklearn_activity_model.py tests/unit/application/test_validate_activity_model.py -v
uv run ruff check src/egfr_discovery/domain/prediction.py src/egfr_discovery/application/ports/activity_model.py src/egfr_discovery/adapters/outbound/ml/sklearn_activity_model.py src/egfr_discovery/application/use_cases/train_activity_model.py src/egfr_discovery/application/use_cases/validate_activity_model.py
uv run mypy src/egfr_discovery/domain/prediction.py src/egfr_discovery/application/ports/activity_model.py src/egfr_discovery/application/use_cases/train_activity_model.py src/egfr_discovery/application/use_cases/validate_activity_model.py
```

Expected: focused tests and core static checks pass; adapter stub limitations, if any, are narrowly annotated rather than globally ignored.

### Task 4: Complete the deterministic screening services and adapters

**Files:**
- Modify: `src/egfr_discovery/application/dto/screening.py`
- Modify: `src/egfr_discovery/application/ports/molecular_fingerprints.py`
- Modify: `src/egfr_discovery/application/use_cases/import_screening_library.py`
- Modify: `src/egfr_discovery/application/use_cases/calculate_compound_properties.py`
- Modify: `src/egfr_discovery/application/use_cases/filter_candidates.py`
- Modify: `src/egfr_discovery/application/use_cases/select_diverse_candidates.py`
- Modify: `src/egfr_discovery/application/use_cases/rank_candidates.py`
- Modify: `src/egfr_discovery/adapters/outbound/chemistry/rdkit_fingerprints.py`
- Modify: `src/egfr_discovery/adapters/outbound/persistence/csv_screening_library.py`
- Test: `tests/unit/application/test_screening_services.py`
- Test: `tests/integration/chemistry/test_rdkit_fingerprints.py`
- Test: `tests/unit/adapters/test_csv_screening_library.py`

- [ ] **Step 1: Write failing tests for strict CSV import, fingerprints, filtering, diversity, and ranking**

Required assertions:

```python
def test_csv_source_requires_compound_id_and_smiles(tmp_path: Path) -> None:
    source = CsvScreeningLibrarySource()
    invalid = tmp_path / "library.csv"
    invalid.write_text("compound_id\nCMP-1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="compound_id, smiles"):
        source.load(str(invalid))


def test_fingerprint_similarity_is_one_for_identical_smiles() -> None:
    calculator = RDKitFingerprintCalculator()
    fingerprint = calculator.fingerprint("CCO")
    assert calculator.similarity(fingerprint, fingerprint) == pytest.approx(1.0)


def test_fingerprint_rejects_invalid_smiles() -> None:
    with pytest.raises(ValueError, match="Invalid SMILES"):
        RDKitFingerprintCalculator().fingerprint("not-smiles")
```

Service tests assert typed `EvaluatedCandidate` inputs, explicit thresholds, stable descending ranks, retained compound/descriptor/prediction evidence, and deterministic diversity order.

- [ ] **Step 2: Run the focused tests and verify current incomplete implementations fail**

Run: `uv run pytest tests/unit/application/test_screening_services.py tests/integration/chemistry/test_rdkit_fingerprints.py tests/unit/adapters/test_csv_screening_library.py -v`

Expected: failures from the empty fingerprint adapter, missing types, and missing CSV validation.

- [ ] **Step 3: Implement the typed services and adapters**

`ScreeningLibrary` retains `library_id`, compounds, and source path. `EvaluatedCandidate` retains prediction and `CandidateProperties`. `RankedCandidate` retains compound ID, SMILES, predicted pIC50, uncertainty, properties, score, and source library ID.

`RDKitFingerprintCalculator` also implements `MolecularStructureValidator`; it uses RDKit Morgan fingerprints and `DataStructs.TanimotoSimilarity`. CSV loading verifies file existence, verifies both required headers before iterating, rejects blank fields through the domain `Compound`, and returns source provenance. Filtering and ranking thresholds remain explicit constructor values; no scientific record is silently dropped without the pipeline counting the stage reduction.

- [ ] **Step 4: Verify focused screening tests**

Run: `uv run pytest tests/unit/application/test_screening_services.py tests/integration/chemistry/test_rdkit_fingerprints.py tests/unit/adapters/test_csv_screening_library.py -v`

Expected: all focused tests pass.

### Task 5: Add artifact persistence and the application orchestrator

**Files:**
- Create: `src/egfr_discovery/application/ports/screening_artifacts.py`
- Create: `src/egfr_discovery/adapters/outbound/persistence/filesystem_screening_artifacts.py`
- Create: `src/egfr_discovery/application/use_cases/run_screening_pipeline.py`
- Modify: `src/egfr_discovery/application/dto/screening.py`
- Test: `tests/unit/adapters/test_filesystem_screening_artifacts.py`
- Test: `tests/integration/screening/test_run_screening_pipeline.py`

- [ ] **Step 1: Write failing artifact and end-to-end orchestration tests**

The artifact test must assert raw JSON preserves original external values and metadata, curation JSON includes each rejection reason, processed CSV retains accepted source identifiers and IC50, and ranked CSV includes rank, compound ID, SMILES, predicted pIC50, uncertainty, descriptors, score, library source, and disclaimer.

The pipeline integration test supplies a fake `BioactivitySource` with at least six unique valid compounds, a temporary library CSV, a permissive validation MAE threshold, real curation/splitting/model/RDKit services, and the filesystem artifact adapter. It asserts every stage count, all output paths exist, no train/validation leakage occurs, and the result disclaimer says predictions are not experimentally validated.

- [ ] **Step 2: Run focused tests and verify missing orchestrator/port failures**

Run: `uv run pytest tests/unit/adapters/test_filesystem_screening_artifacts.py tests/integration/screening/test_run_screening_pipeline.py -v`

Expected: import failures for the artifact port, adapter, and pipeline use case.

- [ ] **Step 3: Implement the artifact port, filesystem adapter, command/result, and orchestrator**

Use this command boundary:

```python
class ScreeningPipelineCommand(BaseModel):
    library_path: Path
    target_id: str = Field(default="CHEMBL203", min_length=1)
    activity_type: str = Field(default="IC50", min_length=1)
    validation_fraction: float = Field(default=0.2, gt=0.0, lt=1.0)
    random_seed: int = 42
    max_validation_mae: float = Field(default=1.0, gt=0.0)
    shortlist_size: int = Field(default=100, gt=0)
    similarity_threshold: float = Field(default=0.7, gt=0.0, le=1.0)
    top_n: int = Field(default=20, gt=0)
    output_path: Path = Path("artifacts/screening/ranked_candidates.csv")
```

The orchestrator receives every dependency in its constructor, logs each stage, writes raw and curation artifacts before model validation, raises `ModelValidationFailed` before screening if validation fails, writes ranked results only after successful completion, and returns a typed `ScreeningPipelineResult` containing counts, paths, validation result, ranked candidates, and the research disclaimer.

- [ ] **Step 4: Run focused pipeline tests and static checks**

Run:

```bash
uv run pytest tests/unit/adapters/test_filesystem_screening_artifacts.py tests/integration/screening/test_run_screening_pipeline.py -v
uv run ruff check src/egfr_discovery/application/ports/screening_artifacts.py src/egfr_discovery/adapters/outbound/persistence/filesystem_screening_artifacts.py src/egfr_discovery/application/use_cases/run_screening_pipeline.py src/egfr_discovery/application/dto/screening.py
```

Expected: artifact and orchestration tests pass with no live network access.

### Task 6: Correct bootstrap commands, resource cleanup, logging, and CLI

**Files:**
- Replace: `src/egfr_discovery/bootstrap/screening_pipeline.py`
- Modify: `src/egfr_discovery/adapters/outbound/chembl/client.py`
- Create: `src/egfr_discovery/bootstrap/logging.py`
- Create: `src/egfr_discovery/adapters/inbound/cli/screen.py`
- Modify: `pyproject.toml`
- Modify: `.gitignore`
- Test: `tests/unit/bootstrap/test_screening_pipeline.py`
- Test: `tests/unit/cli/test_screen.py`

- [ ] **Step 1: Write failing bootstrap and CLI tests**

Bootstrap tests patch adapter constructors and assert each imported class is instantiated and injected under matching names. They assert the same model instance is used by train, validation, and screen use cases and that `ChEMBLClient.close()` runs on success and error.

CLI tests invoke the Typer app with a temporary library and a patched `run_pipeline`, then assert validated arguments, result paths/counts, and this exact warning:

```text
Research prediction only; candidates are not experimentally validated medicines or clinical recommendations.
```

- [ ] **Step 2: Run focused tests and verify current undefined command variables fail**

Run: `uv run pytest tests/unit/bootstrap/test_screening_pipeline.py tests/unit/cli/test_screen.py -v`

Expected: failures because current bootstrap references undefined lower-case commands and no screen CLI exists.

- [ ] **Step 3: Implement dependency construction and executable command**

`ChEMBLClient` receives a string base URL, owns the HTTPX client, and implements `__enter__`, `__exit__`, and idempotent `close`. `build_screening_pipeline(client, command)` explicitly constructs and names every dependency. `run_pipeline(command)` wraps the client in a context manager and returns `pipeline.execute(command)`.

`configure_logging()` creates `logs/egfr-screen-YYYYMMDDTHHMMSSZ.log`, installs UTF-8 file and console handlers with timestamps, and returns the path. `screen.py` uses Typer, builds `ScreeningPipelineCommand`, calls bootstrap, prints the top `min(top_n, len(ranked))` candidates and the warning. Register:

```toml
[project.scripts]
egfr-hex = "egfr_discovery.main:main"
egfr-screen = "egfr_discovery.adapters.inbound.cli.screen:main"
```

Add `logs/*.log` to `.gitignore`.

- [ ] **Step 4: Verify bootstrap, CLI, command help, and imports**

Run:

```bash
uv run pytest tests/unit/bootstrap/test_screening_pipeline.py tests/unit/cli/test_screen.py -v
uv run egfr-screen --help
uv run python -c "import egfr_discovery.bootstrap.screening_pipeline"
```

Expected: tests and import pass; help lists the required `--library` option and all documented options.

### Task 7: Repository verification and focused cleanup

**Files:**
- Review all files listed above.

- [ ] **Step 1: Format only the screening files changed by this plan**

Run `uv run ruff format` with the explicit changed source and test paths. Do not format unrelated files.

- [ ] **Step 2: Run the full verification suite**

Run:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
uv run lint-imports
git diff --check
```

Expected: all new tests pass. Any remaining failures must be classified as introduced by this work or pre-existing, and introduced failures must be fixed before completion.

- [ ] **Step 3: Perform a live-free command smoke test**

Run `uv run egfr-screen --help` and the integration test rather than contacting ChEMBL. Record that live ChEMBL availability, remote schema changes, and predictive quality remain external risks.

- [ ] **Step 4: Review and commit only intended changes**

Review `git diff`, confirm no `.env`, generated artifacts, logs, caches, or unrelated agent files are staged, then commit the implementation and tests with:

```bash
git add .gitignore pyproject.toml src/egfr_discovery/domain/bioactivity.py src/egfr_discovery/domain/prediction.py src/egfr_discovery/application/dto/external_bioactivity.py src/egfr_discovery/application/dto/screening.py src/egfr_discovery/application/ports/activity_model.py src/egfr_discovery/application/ports/bioactivity_source_data.py src/egfr_discovery/application/ports/molecular_fingerprints.py src/egfr_discovery/application/ports/molecular_structure.py src/egfr_discovery/application/ports/screening_artifacts.py src/egfr_discovery/application/ports/screening_library_source.py src/egfr_discovery/application/use_cases/calculate_compound_properties.py src/egfr_discovery/application/use_cases/curate_bioactivity_dataset.py src/egfr_discovery/application/use_cases/filter_candidates.py src/egfr_discovery/application/use_cases/import_screening_library.py src/egfr_discovery/application/use_cases/ingest_bioactivity_data.py src/egfr_discovery/application/use_cases/rank_candidates.py src/egfr_discovery/application/use_cases/run_screening_pipeline.py src/egfr_discovery/application/use_cases/screen_compounds.py src/egfr_discovery/application/use_cases/select_diverse_candidates.py src/egfr_discovery/application/use_cases/split_bioactivity_dataset.py src/egfr_discovery/application/use_cases/train_activity_model.py src/egfr_discovery/application/use_cases/validate_activity_model.py src/egfr_discovery/adapters/inbound/cli/screen.py src/egfr_discovery/adapters/outbound/chembl/bioactivity_source_data.py src/egfr_discovery/adapters/outbound/chembl/client.py src/egfr_discovery/adapters/outbound/chemistry/rdkit_fingerprints.py src/egfr_discovery/adapters/outbound/ml/sklearn_activity_model.py src/egfr_discovery/adapters/outbound/persistence/csv_screening_library.py src/egfr_discovery/adapters/outbound/persistence/filesystem_screening_artifacts.py src/egfr_discovery/bootstrap/ingest.py src/egfr_discovery/bootstrap/logging.py src/egfr_discovery/bootstrap/screening_pipeline.py tests/unit/application tests/unit/adapters tests/unit/bootstrap tests/unit/cli tests/integration/chemistry/test_rdkit_fingerprints.py tests/integration/screening
git commit -m "Make screening pipeline executable"
```
