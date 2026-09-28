# Executable Screening Pipeline Design

## Goal

Make the EGFR screening workflow executable from bioactivity retrieval through ranked-candidate export while aligning every command, import, data contract, and dependency with the repository's hexagonal architecture.

The workflow produces computational research predictions only. Its output must explicitly state that ranked candidates are not experimentally validated medicines or clinical recommendations.

## Architecture

Orchestration belongs in a new application use case. `bootstrap/screening_pipeline.py` will construct concrete adapters and inject them into that use case; it will not contain scientific calculations. A thin inbound CLI adapter will validate user inputs and invoke bootstrap.

Dependency direction remains:

1. Domain objects depend only on the standard library.
2. Application DTOs, ports, and use cases depend on domain objects and abstract ports.
3. Outbound adapters implement ports using ChEMBL, HTTPX, RDKit, sklearn, joblib, and CSV.
4. Bootstrap imports both application abstractions and concrete adapters to assemble the graph.

Application code will no longer import ChEMBL adapter schemas or RDKit directly.

## Public Command

Add an `egfr-screen` project script with this conceptual interface:

```text
egfr-screen --library PATH [--target-id CHEMBL203] [--activity-type IC50]
            [--validation-fraction 0.2] [--random-seed 42]
            [--max-validation-mae 1.0] [--shortlist-size 100]
            [--top-n 20] [--output PATH]
```

The screening-library CSV is required. The project will not invent example screening compounds or silently reuse training compounds as screening inputs.

The CLI will convert arguments into a Pydantic boundary model, invoke the pipeline, print output locations and counts, and display the research-only disclaimer.

## Boundary Models and Results

`ScreeningPipelineCommand` will validate:

- A required screening-library path.
- Non-empty target and activity identifiers.
- Validation fraction strictly between zero and one.
- Positive validation MAE threshold.
- Positive shortlist and displayed-result limits.
- An explicit output CSV path with a safe default under `artifacts/screening/`.

`ScreeningPipelineResult` will report the raw, accepted, rejected, screened, filtered, shortlisted, and ranked record counts; model validation metrics; model and result paths; and ranked candidates.

## Data Flow

The application orchestrator will execute these stages in order:

1. Fetch external activity records through `BioactivitySource`.
2. Persist the unmodified source snapshot and source metadata through an output port.
3. Curate records into domain `BioactivityMeasurement` values while recording every rejection reason.
4. Persist the curation report and processed dataset.
5. Split the curated data deterministically by compound identifier, preventing the same compound from appearing in training and validation sets.
6. Fit a pIC50 regression model on the training set.
7. Validate predicted pIC50 values on the held-out set and stop on failed acceptance criteria.
8. Import the caller-supplied screening library through `ScreeningLibrarySource`.
9. Predict pIC50 for every screening compound.
10. Calculate deterministic molecular descriptors.
11. Apply explicit potency and property filters.
12. Select a structurally diverse shortlist using RDKit fingerprints and a configurable similarity threshold.
13. Rank candidates using potency, properties, and model uncertainty.
14. Persist ranked results with source identifiers, SMILES, predictions, uncertainty, descriptors, score, rank, and provenance.

Each stage will log its start, completion, and record counts. Invalid scientific records will be represented in the curation report rather than silently discarded.

## Contract Corrections

### Bioactivity source

`BioactivitySource` will return application-owned `ExternalBioactivityRecord` objects. The ChEMBL adapter will translate its Pydantic response schema to that DTO. This removes the current application-to-adapter dependency.

### Curation

The curation use case will return both a non-empty `CuratedDataset` and structured rejection information. Original external values remain in the raw snapshot, and rejection records retain their source record and reason.

### Dataset splitting

Add a `SplitBioactivityDataset` use case. It will group measurements by compound ID, apply a deterministic seeded shuffle, and create non-empty train and validation datasets with no compound leakage. Insufficient unique compounds will raise a clear validation error.

### Activity model

The `ActivityModel` port and sklearn adapter will consistently implement `fit`, `predict`, and `save`. The adapter will be a regression model trained on pIC50 values, not a binary classifier whose probabilities are mislabeled as potency.

`ActivityPrediction` will expose `predicted_pic50` plus optional non-negative uncertainty. No code will claim the prediction is measured or validated activity.

### Fingerprints

Implement `RDKitFingerprintCalculator` behind `MolecularFingerprintCalculator`. Invalid SMILES will raise a clear error; they will not be skipped.

### Screening candidates

Property calculation, filtering, diversity selection, and ranking will use concrete typed inputs and outputs. Ranked candidates will retain the underlying compound, prediction, descriptors, and provenance needed for export.

## Bootstrap Wiring

`bootstrap/screening_pipeline.py` will instantiate each imported component before use:

- `ChEMBLClient` and `ChEMBLBioactivitySource`.
- Curation and compound-level split use cases.
- A single shared `SklearnActivityModel` for training, validation, and screening.
- CSV screening-library adapter.
- RDKit descriptor and fingerprint adapters.
- Filter, diversity, and ranking use cases.
- Filesystem result/snapshot adapter.
- The application pipeline orchestrator.

`run_pipeline(command)` will construct the graph and return the pipeline result. All local command names will match the imported class names and public methods.

## Error Handling

- HTTP failures propagate with ChEMBL request context after resources are closed.
- Missing or malformed CSV columns raise errors naming the file and required columns.
- Invalid ChEMBL records are preserved in the raw snapshot and represented in the rejection report.
- Empty curated datasets, insufficient split groups, invalid SMILES, untrained models, and failed validation raise explicit exceptions.
- Model-validation failure prevents screening and result export.
- Output directories are created explicitly; write errors are never swallowed.
- The ChEMBL client supports context-managed cleanup.

## Logging

The CLI will configure standard-library logging with:

- A timestamped UTF-8 logfile under `logs/`.
- Console messages for function/stage execution.
- Counts, file paths, validation metrics, and failures.
- No secrets or complete scientific datasets in logs.

No new logging dependency is required.

## Testing

Tests will be added before implementation and will cover:

- ChEMBL-to-application DTO mapping.
- Explicit curation acceptance and rejection reasons.
- Deterministic compound-group splitting with no leakage.
- Regression model fit, pIC50 prediction, uncertainty, and persistence.
- Invalid/untrained model behavior.
- RDKit fingerprint generation, similarity, and invalid SMILES.
- Screening-library required-column validation and source provenance.
- Typed property calculation, filtering, diversity selection, and ranking.
- Pipeline order, validation gating, output persistence, and result counts using fakes and temporary files.
- Bootstrap import and construction.
- CLI argument validation and research-only messaging.

The end-to-end automated test will not call the live ChEMBL service. It will use a fake source with source-shaped records and a temporary screening CSV, while exercising real deterministic scientific services where practical.

## Scope and Dependencies

The work will correct only files required to make the screening path coherent and executable. Existing unrelated agents and experimental modules will not be refactored.

No new runtime dependency is expected: Pydantic, HTTPX, RDKit, sklearn, joblib, and Typer are already declared. If implementation proves that an additional dependency is necessary, it must be explained before being added.
