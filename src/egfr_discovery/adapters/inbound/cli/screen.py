from pathlib import Path
from typing import Annotated

import typer

from egfr_discovery.application.dto.screening import ScreeningPipelineCommand
from egfr_discovery.bootstrap.logging import configure_logging
from egfr_discovery.bootstrap.screening_pipeline import run_pipeline

app = typer.Typer(add_completion=False)
DEFAULT_OUTPUT_PATH = Path("artifacts/screening/ranked_candidates.csv")


@app.command()
def screen(
    library: Annotated[Path, typer.Option("--library", help="Screening library CSV")],
    target_id: Annotated[str, typer.Option("--target-id")] = "CHEMBL203",
    activity_type: Annotated[str, typer.Option("--activity-type")] = "IC50",
    validation_fraction: Annotated[float, typer.Option("--validation-fraction")] = 0.2,
    random_seed: Annotated[int, typer.Option("--random-seed")] = 42,
    max_validation_mae: Annotated[float, typer.Option("--max-validation-mae")] = 1.0,
    shortlist_size: Annotated[int, typer.Option("--shortlist-size")] = 100,
    similarity_threshold: Annotated[
        float, typer.Option("--similarity-threshold")
    ] = 0.7,
    top_n: Annotated[int, typer.Option("--top-n")] = 20,
    output: Annotated[Path, typer.Option("--output")] = DEFAULT_OUTPUT_PATH,
) -> None:
    log_path = configure_logging()
    command = ScreeningPipelineCommand(
        library_path=library,
        target_id=target_id,
        activity_type=activity_type,
        validation_fraction=validation_fraction,
        random_seed=random_seed,
        max_validation_mae=max_validation_mae,
        shortlist_size=shortlist_size,
        similarity_threshold=similarity_threshold,
        top_n=top_n,
        output_path=output,
    )
    result = run_pipeline(command)
    typer.echo(f"Fetched: {result.fetched_count}")
    typer.echo(f"Curated: {result.curated_count}")
    typer.echo(f"Rejected: {result.rejected_count}")
    typer.echo(f"Screened: {result.screened_count}")
    typer.echo(f"Log: {log_path}")
    for artifact_path in result.artifact_paths:
        typer.echo(f"Artifact: {artifact_path}")
    for candidate in result.ranked_candidates[: command.top_n]:
        typer.echo(
            f"{candidate.rank}. {candidate.compound_id} "
            f"pIC50={candidate.predicted_pic50:.3f} score={candidate.score:.3f}"
        )
    typer.echo(result.disclaimer)


def main() -> None:
    app()
