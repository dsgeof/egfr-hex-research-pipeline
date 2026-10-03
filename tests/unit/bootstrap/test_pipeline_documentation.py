from pathlib import Path

import pytest

from egfr_discovery.application.dto.pipeline_documentation import (
    REQUIRED_PIPELINE_SECTION_KEYS,
)
from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentationCommand,
)
from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
)
from egfr_discovery.bootstrap.pipeline_documentation import (
    PIPELINE_DOCUMENTATION_REGISTRY,
    build_pipeline_documentation_generator,
    run_pipeline_documentation,
)


def test_registry_contains_one_ordered_egfr_screening_description() -> None:
    assert len(PIPELINE_DOCUMENTATION_REGISTRY.pipelines) == 1
    documented = PIPELINE_DOCUMENTATION_REGISTRY.pipelines[0]
    assert documented.pipeline_id == "egfr_screening"
    assert documented.title == "EGFR Small-Molecule Screening Pipeline"
    assert documented.summary
    assert tuple(section.key for section in documented.sections) == (
        REQUIRED_PIPELINE_SECTION_KEYS
    )


@pytest.mark.parametrize(
    ("section_key", "required_phrases"),
    [
        (
            "plain_language_summary",
            (
                "altered",
                "cancers",
                "laboratory measurements",
                "shortlist",
                "laboratory testing is costly",
                "prioritization",
                "research hypotheses, not proof",
            ),
        ),
        (
            "inputs",
            (
                "ChEMBL",
                "EGFR",
                "exact, positive IC50",
                "nM",
                "validates",
                "rejected",
                "reasons",
                "provenance",
                "by compound",
                "caller-provided CSV",
                "compound_id",
                "smiles",
            ),
        ),
        (
            "prediction_and_features",
            (
                "continuous pIC50",
                "negative base-10 logarithm",
                "molar",
                "50% inhibition",
                "character-level TF-IDF",
                "one through three",
                "SMILES",
                "measured binding",
                "three-dimensional binding pose",
                "safety",
                "clinical efficacy",
            ),
        ),
        (
            "models_and_rationale",
            (
                "deterministic",
                "RandomForestRegressor",
                "nonlinear",
                "population standard deviation",
                "tree predictions",
                "dispersion",
                "not calibrated experimental uncertainty",
            ),
        ),
        (
            "drug_discovery_use",
            (
                "deterministic molecular descriptors",
                "property filters",
                "Morgan",
                "diversity",
                "ranking",
                "predicted potency",
                "properties",
                "dispersion",
                "expert review",
                "experimental testing",
            ),
        ),
        (
            "drug_discovery_value",
            (
                "reduce a large library",
                "experimental resources",
                "do not establish potency, selectivity, safety, developability",
                "clinical utility",
                "clinical recommendation",
            ),
        ),
    ],
)
def test_registry_explains_implemented_science_and_limitations(
    section_key: str, required_phrases: tuple[str, ...]
) -> None:
    documented = PIPELINE_DOCUMENTATION_REGISTRY.pipelines[0]
    sections = {section.key: section.body for section in documented.sections}
    for phrase in required_phrases:
        assert phrase in sections[section_key]


def test_builder_writes_registered_content_through_filesystem(tmp_path: Path) -> None:
    destination = tmp_path / "docs" / "pipelines.md"
    generator = build_pipeline_documentation_generator()
    result = generator.execute(
        GeneratePipelineDocumentationCommand(destination=destination)
    )
    assert result.changed
    assert result.destination == destination
    assert destination.read_text(encoding="utf-8") == render_pipeline_documentation(
        PIPELINE_DOCUMENTATION_REGISTRY
    )


def test_runner_builds_generator_and_returns_check_result(tmp_path: Path) -> None:
    destination = tmp_path / "pipelines.md"
    destination.write_text(
        render_pipeline_documentation(PIPELINE_DOCUMENTATION_REGISTRY),
        encoding="utf-8",
    )
    result = run_pipeline_documentation(
        GeneratePipelineDocumentationCommand(destination=destination, check=True)
    )
    assert result.destination == destination
    assert result.checked
    assert not result.changed
