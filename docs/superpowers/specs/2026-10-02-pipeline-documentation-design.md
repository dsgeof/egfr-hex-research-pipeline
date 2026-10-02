# Generated Pipeline Documentation Design

## Goal

Add an extensible, deterministic developer tool that generates a root-level
`pipelines.md` describing every registered end-to-end screening pipeline.
The initial document will describe the existing EGFR screening pipeline using
the five scientific and drug-discovery topics requested by the project owner.

## Scope

This feature documents end-to-end screening pipelines only. The ingestion and
model-training commands are stages of the current screening pipeline, not
separate documented pipelines.

The feature will:

- Define typed pipeline and section metadata.
- Register the existing EGFR screening pipeline.
- Render all registered pipelines to deterministic Markdown.
- Provide a developer command that writes root-level `pipelines.md`.
- Provide a non-mutating check mode that detects a missing or stale document.
- Test the metadata, renderer, registry content, CLI, and committed output.

The feature will not:

- Change pipeline execution or scientific calculations.
- Generate documentation during a screening run.
- Contact ChEMBL, train a model, or screen compounds while generating docs.
- Treat predictions as experimentally validated results or clinical advice.

## Architecture

Pipeline documentation will be a runtime-independent support subsystem. It
will use three focused components:

1. Typed metadata models for a pipeline and its ordered sections.
2. A registry containing the documentation for each end-to-end pipeline.
3. A deterministic Markdown renderer used by a developer-facing CLI.

The renderer will accept documentation values rather than importing concrete
pipeline adapters. The existing pipeline will not import the documentation
subsystem. This keeps documentation generation out of scientific execution
and preserves the repository's hexagonal dependency rules.

The metadata will model sections as an ordered collection rather than five
hard-coded properties. Each section will have a stable key, a display heading,
and Markdown content. The registry will validate the required section keys,
while the renderer will accept additional sections without code changes.

## Metadata contract

Each `PipelineDocumentation` entry will contain:

- A non-empty, stable pipeline ID.
- A non-empty display title.
- A non-empty summary suitable for the document introduction.
- An ordered, non-empty tuple of `PipelineDocumentationSection` values.

Each section will contain:

- A non-empty stable key.
- A non-empty Markdown heading.
- A non-empty Markdown body.

The five required keys will be:

1. `inputs`
2. `prediction_and_features`
3. `models_and_rationale`
4. `drug_discovery_use`
5. `drug_discovery_value`

Validation will reject duplicate pipeline IDs, duplicate section keys, blank
values, and missing required sections. Additional unique sections will be
allowed and rendered in their declared order, making later additions
straightforward.

## Initial EGFR screening content

The first registry entry will document the existing EGFR screening pipeline
accurately and conservatively.

### Input summary

The pipeline uses ChEMBL EGFR IC50 activity records for model development and
a caller-provided CSV screening library containing `compound_id` and `smiles`.
It curates exact, positive IC50 measurements in nM, validates structures,
preserves accepted and rejected provenance, and splits model-development data
by compound identifier to avoid train/validation compound leakage.

### Prediction target and features

The model predicts continuous pIC50 for each screening-library compound. The
model features are character-level TF-IDF n-grams of lengths one through three
derived from the SMILES string. The documentation will not imply that these
features encode experimentally measured binding, three-dimensional poses, or
clinical efficacy.

### Model and rationale

The pipeline uses a deterministic `RandomForestRegressor`. The documentation
will explain that a nonlinear ensemble can model interactions in the sparse
SMILES-derived representation without assuming a linear response. It will
also explain that the population standard deviation across tree predictions
is reported as a model-dispersion uncertainty estimate. This estimate will not
be described as calibrated experimental uncertainty.

### Drug-discovery use

Predicted pIC50 is combined with deterministic molecular descriptors,
property thresholds, fingerprint-based diversity selection, and ranking. The
result is a prioritized, chemically diverse shortlist for further review and
experimental testing.

### Drug-discovery value

The prediction helps reduce a larger screening library to a smaller set of
hypotheses, supports relative prioritization, and exposes model dispersion for
decision-making. The document will state that computational predictions do not
establish potency, safety, selectivity, developability, or clinical utility.

## Generated Markdown

The renderer will produce stable output with:

- A generated-file notice telling contributors which command owns the file.
- A document title and short purpose statement.
- The research-only disclaimer near the beginning.
- One second-level heading per registered pipeline.
- The pipeline summary followed by its ordered section headings and bodies.
- Exactly one trailing newline.

Pipeline order will follow registry order. Section order will follow the
metadata declaration. The renderer will not include timestamps or other
volatile values, so identical metadata produces byte-identical Markdown.

## Developer command

The project will register an `egfr-pipeline-docs` command.

Default mode:

```bash
uv run egfr-pipeline-docs
```

This command renders the registry and writes `pipelines.md` relative to the
repository working directory. It creates or replaces only that file and
prints its path.

Check mode:

```bash
uv run egfr-pipeline-docs --check
```

Check mode reads `pipelines.md` without modifying it. It exits successfully
only when the file exists and is byte-for-byte equal to freshly rendered
content. A missing or stale file produces a concise error and a non-zero exit
status instructing the developer to run the write command.

## Error handling

Metadata validation errors will identify the pipeline and invalid or missing
section. Duplicate pipeline IDs will be detected before rendering. Filesystem
errors will propagate with their original path and cause. Check mode will
distinguish a missing document from stale content.

Generation will never silently omit an invalid pipeline or section. One
invalid registry entry prevents the document from being written.

## Testing

Unit tests will verify:

- Blank metadata is rejected.
- Duplicate section keys are rejected.
- Duplicate pipeline IDs are rejected.
- Missing required sections are rejected.
- An additional custom section is accepted and rendered in order.
- Rendering is deterministic and contains the generated-file notice and
  research-only disclaimer.
- The EGFR registry entry names pIC50, character-level SMILES TF-IDF n-grams,
  `RandomForestRegressor`, tree-level model dispersion, descriptor filtering,
  fingerprint diversity selection, ranking, and experimental follow-up.

CLI tests will verify:

- Default mode writes the expected root-level Markdown.
- Check mode succeeds for current content.
- Check mode fails without modifying a missing or stale document.

A synchronization test will compare freshly rendered content with the
committed root-level `pipelines.md`. Documentation tests will not access the
network, train models, or execute the screening pipeline.

Repository verification will run the full test suite, Ruff, mypy, the
architecture contracts, the generation check command, and `git diff --check`.

## Extension workflow

To document a new end-to-end screening pipeline, a contributor will add one
typed registry entry with the five required sections, add any pipeline-specific
sections, regenerate `pipelines.md`, and run check mode. To add a new required
topic globally, the contributor will add its stable key to the required-key
collection and provide that section for every registered pipeline. The
Markdown renderer will not require modification in either case.
