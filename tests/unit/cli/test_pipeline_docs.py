from pathlib import Path

import pytest
from typer.testing import CliRunner

from egfr_discovery.adapters.inbound.cli.pipeline_docs import app
from egfr_discovery.application.use_cases.render_pipeline_documentation import (
    render_pipeline_documentation,
)
from egfr_discovery.bootstrap.pipeline_documentation import (
    PIPELINE_DOCUMENTATION_REGISTRY,
)


def test_cli_writes_root_document(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0, result.output
    assert "Wrote pipelines.md" in result.stdout
    assert (tmp_path / "pipelines.md").read_text(encoding="utf-8") == (
        render_pipeline_documentation(PIPELINE_DOCUMENTATION_REGISTRY)
    )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [([], "pipelines.md is already current"), (["--check"], "pipelines.md is current")],
)
def test_cli_leaves_current_document_untouched(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    arguments: list[str],
    message: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "pipelines.md"
    original = render_pipeline_documentation(PIPELINE_DOCUMENTATION_REGISTRY)
    destination.write_text(original, encoding="utf-8")
    original_mtime = destination.stat().st_mtime_ns
    result = CliRunner().invoke(app, arguments)
    assert result.exit_code == 0, result.output
    assert message in result.stdout
    assert destination.read_text(encoding="utf-8") == original
    assert destination.stat().st_mtime_ns == original_mtime
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.parametrize("existing_content", [None, "stale\n"])
def test_cli_check_reports_missing_or_stale_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    existing_content: str | None,
) -> None:
    monkeypatch.chdir(tmp_path)
    destination = tmp_path / "pipelines.md"
    if existing_content is not None:
        destination.write_text(existing_content, encoding="utf-8")
    result = CliRunner().invoke(app, ["--check"])
    assert result.exit_code == 1
    expected_state = "missing" if existing_content is None else "stale"
    assert f"Pipeline documentation is {expected_state}: pipelines.md" in result.stderr
    assert "Run `uv run egfr-pipeline-docs` to regenerate it." in result.stderr
    assert not result.stdout
    if existing_content is None:
        assert not list(tmp_path.iterdir())
    else:
        assert destination.read_text(encoding="utf-8") == existing_content
        assert list(tmp_path.iterdir()) == [destination]


def test_cli_help_exposes_check_option() -> None:
    result = CliRunner().invoke(app, ["--help"], color=False)
    assert result.exit_code == 0, result.output
    assert "--check" in result.output
