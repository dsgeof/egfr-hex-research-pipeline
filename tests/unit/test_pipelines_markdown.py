from pathlib import Path

from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
)
from egfr_discovery.bootstrap.pipeline_documentation import (
    PIPELINE_DOCUMENTATION_REGISTRY,
)


def test_pipelines_markdown_matches_registered_documentation() -> None:
    repository_root = Path(__file__).parents[2]
    with (repository_root / "pipelines.md").open(
        encoding="utf-8", newline=""
    ) as handle:
        committed_documentation = handle.read()

    assert committed_documentation == render_pipeline_documentation(
        PIPELINE_DOCUMENTATION_REGISTRY
    )
