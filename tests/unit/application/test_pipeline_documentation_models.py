import pytest
from pydantic import ValidationError

from egfr_discovery.application.dto.pipeline_documentation import (
    REQUIRED_PIPELINE_SECTION_KEYS,
    PipelineDocumentation,
    PipelineDocumentationRegistry,
    PipelineDocumentationSection,
)


def build_section(key: str) -> PipelineDocumentationSection:
    return PipelineDocumentationSection(
        key=key,
        heading=key.replace("_", " ").title(),
        body=f"Body for {key}.",
    )


def build_sections() -> tuple[PipelineDocumentationSection, ...]:
    return tuple(build_section(key) for key in REQUIRED_PIPELINE_SECTION_KEYS)


def build_documentation(
    *,
    pipeline_id: str = "pipeline-1",
    sections: tuple[PipelineDocumentationSection, ...] | None = None,
) -> PipelineDocumentation:
    return PipelineDocumentation(
        pipeline_id=pipeline_id,
        title="Pipeline documentation",
        summary="A plain-language pipeline summary.",
        sections=build_sections() if sections is None else sections,
    )


@pytest.mark.parametrize("field", ["key", "heading", "body"])
def test_section_rejects_non_string_or_whitespace_only_values(field: str) -> None:
    values = {"key": "key", "heading": "Heading", "body": "Body"}
    values[field] = "  \t  "

    with pytest.raises(ValidationError):
        PipelineDocumentationSection(**values)


def test_documentation_rejects_missing_required_section_and_names_key() -> None:
    sections = tuple(
        build_section(key) for key in REQUIRED_PIPELINE_SECTION_KEYS if key != "inputs"
    )

    with pytest.raises(ValidationError, match="inputs"):
        build_documentation(sections=sections)


def test_plain_language_summary_must_be_first_section() -> None:
    sections = (
        build_section("inputs"),
        build_section("plain_language_summary"),
        *build_sections()[2:],
    )

    with pytest.raises(ValidationError, match="plain_language_summary"):
        build_documentation(sections=sections)


def test_documentation_rejects_duplicate_section_keys() -> None:
    sections = (*build_sections(), build_section("inputs"))

    with pytest.raises(ValidationError, match="Duplicate section key"):
        build_documentation(sections=sections)


def test_registry_rejects_duplicate_pipeline_ids() -> None:
    pipelines = (build_documentation(), build_documentation(pipeline_id="pipeline-1"))

    with pytest.raises(ValidationError, match="Duplicate pipeline id"):
        PipelineDocumentationRegistry(pipelines=pipelines)


def test_additional_section_is_accepted_and_remains_last() -> None:
    limitations = build_section("limitations")
    documentation = build_documentation(sections=(*build_sections(), limitations))

    assert documentation.sections[-1] == limitations
    assert tuple(section.key for section in documentation.sections) == (
        *REQUIRED_PIPELINE_SECTION_KEYS,
        "limitations",
    )
