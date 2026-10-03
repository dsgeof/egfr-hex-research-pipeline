from typing import Annotated

import typer

from egfr_discovery.application.use_cases.generate_pipeline_documentation import (
    GeneratePipelineDocumentationCommand,
    PipelineDocumentationMissing,
    PipelineDocumentationStale,
)
from egfr_discovery.bootstrap.pipeline_documentation import run_pipeline_documentation

app = typer.Typer(add_completion=False)


@app.command()
def generate(
    check: Annotated[
        bool,
        typer.Option("--check", help="Check documentation without changing files."),
    ] = False,
) -> None:
    """Generate pipelines.md from the registered pipeline descriptions."""
    try:
        result = run_pipeline_documentation(
            GeneratePipelineDocumentationCommand(check=check)
        )
    except (PipelineDocumentationMissing, PipelineDocumentationStale) as error:
        typer.echo(str(error), err=True)
        typer.echo("Run `uv run egfr-pipeline-docs` to regenerate it.", err=True)
        raise typer.Exit(code=1) from error

    if result.checked:
        typer.echo(f"{result.destination} is current")
    elif result.changed:
        typer.echo(f"Wrote {result.destination}")
    else:
        typer.echo(f"{result.destination} is already current")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
