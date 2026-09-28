from pathlib import Path

from typer.testing import CliRunner

from egfr_discovery.adapters.inbound.cli import screen
from egfr_discovery.application.dto.model_results import (
    ModelValidationResult,
    RegressionMetrics,
)
from egfr_discovery.application.dto.screening import (
    RankedCandidate,
    ScreeningPipelineResult,
)
from egfr_discovery.application.use_cases.run_screening_pipeline import (
    RESEARCH_DISCLAIMER,
)
from egfr_discovery.domain.candidate import CandidateProperties


def test_cli_builds_command_and_prints_research_warning(
    monkeypatch, tmp_path: Path
) -> None:
    library = tmp_path / "library.csv"
    library.write_text("compound_id,smiles\nCMP-1,CCO\n", encoding="utf-8")
    captured = []

    def fake_run(command):
        captured.append(command)
        return ScreeningPipelineResult(
            fetched_count=6,
            curated_count=5,
            rejected_count=1,
            screened_count=1,
            filtered_count=1,
            diverse_count=1,
            validation=ModelValidationResult(
                True, RegressionMetrics(0.1, 0.2, 0.8), ()
            ),
            ranked_candidates=(
                RankedCandidate(
                    rank=1,
                    compound_id="CMP-1",
                    smiles="CCO",
                    predicted_pic50=7.5,
                    uncertainty=0.2,
                    properties=CandidateProperties(46.1, -0.1, 1, 1, 20.2),
                    score=0.8,
                    source_library_id="library",
                ),
            ),
            artifact_paths=(str(tmp_path / "ranked.csv"),),
            disclaimer=RESEARCH_DISCLAIMER,
        )

    monkeypatch.setattr(screen, "run_pipeline", fake_run)
    monkeypatch.setattr(screen, "configure_logging", lambda: tmp_path / "run.log")

    output_path = tmp_path / "results.csv"
    result = CliRunner().invoke(
        screen.app,
        [
            "--library",
            str(library),
            "--target-id",
            "CHEMBL999",
            "--shortlist-size",
            "5",
            "--top-n",
            "1",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured[0].library_path == library
    assert captured[0].target_id == "CHEMBL999"
    assert captured[0].shortlist_size == 5
    assert captured[0].output_path == output_path
    assert "Fetched: 6" in result.output
    assert "CMP-1 pIC50=7.500 score=0.800" in result.output
    assert f"Artifact: {tmp_path / 'ranked.csv'}" in result.output
    assert RESEARCH_DISCLAIMER in result.output
