from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
    model_validator,
)

REQUIRED_PIPELINE_SECTION_KEYS = (
    "plain_language_summary",
    "inputs",
    "prediction_and_features",
    "models_and_rationale",
    "drug_discovery_use",
    "drug_discovery_value",
)


def _strip_non_blank(value: object, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")  # noqa: TRY004
    stripped_value = value.strip()
    if not stripped_value:
        raise ValueError(f"{field_name} must not be blank")
    return stripped_value


class PipelineDocumentationSection(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    heading: str
    body: str

    @field_validator("key", "heading", "body", mode="before")
    @classmethod
    def validate_text(cls, value: object, info: ValidationInfo) -> str:
        field_name = info.field_name or "value"
        return _strip_non_blank(value, field_name=field_name)


class PipelineDocumentation(BaseModel):
    model_config = ConfigDict(frozen=True)

    pipeline_id: str
    title: str
    summary: str
    sections: tuple[PipelineDocumentationSection, ...]

    @field_validator("pipeline_id", "title", "summary", mode="before")
    @classmethod
    def validate_text(cls, value: object, info: ValidationInfo) -> str:
        field_name = info.field_name or "value"
        return _strip_non_blank(value, field_name=field_name)

    @model_validator(mode="after")
    def validate_sections(self) -> Self:
        section_keys = tuple(section.key for section in self.sections)
        seen_keys: set[str] = set()
        for key in section_keys:
            if key in seen_keys:
                raise ValueError(f"Duplicate section key: {key}")
            seen_keys.add(key)

        missing_keys = tuple(
            key for key in REQUIRED_PIPELINE_SECTION_KEYS if key not in seen_keys
        )
        if missing_keys:
            raise ValueError(
                "Missing required section key(s): " + ", ".join(missing_keys)
            )

        if self.sections and self.sections[0].key != "plain_language_summary":
            raise ValueError("The first section must have key plain_language_summary")
        return self


class PipelineDocumentationRegistry(BaseModel):
    model_config = ConfigDict(frozen=True)

    pipelines: tuple[PipelineDocumentation, ...]

    @model_validator(mode="after")
    def validate_pipeline_ids(self) -> Self:
        seen_ids: set[str] = set()
        for pipeline in self.pipelines:
            if pipeline.pipeline_id in seen_ids:
                raise ValueError(f"Duplicate pipeline id: {pipeline.pipeline_id}")
            seen_ids.add(pipeline.pipeline_id)
        return self
