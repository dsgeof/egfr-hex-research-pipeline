# Project instructions

## Project purpose

This repository implements an agentic virtual-screening platform for
identifying potential small-molecule inhibitors of mutant EGFR.

The software is for research and educational purposes. It must not present
computational predictions as validated medicines or clinical recommendations.

## Architecture

The project uses hexagonal architecture.

- Domain code may import only Python standard-library modules.
- Application code may import domain code.
- Application code must not import concrete adapters.
- External systems are accessed through application ports.
- Adapters implement those ports.
- Dependency construction belongs in bootstrap.
- LLM agents must not contain deterministic scientific calculations.
- Agents may propose, explain and critique.
- Python services calculate, validate and enforce.

## Engineering rules

- Use Python type hints.
- Use Pydantic for application boundary schemas.
- Add logging to a timestamped logfile and log function execution to the console.
- Add tests for every behavior.
- Do not refactor unrelated code.
- Do not add dependencies without explaining why.
- Keep each task narrowly scoped.
- Never silently discard invalid scientific data.
- Preserve source values and provenance.
- Do not claim predicted activity is experimentally validated.

## Commands

- Install: `uv sync`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type-check: `uv run mypy src`
- Architecture: `uv run lint-imports`

## Completion

Before completing a coding task:

1. Run relevant tests.
2. Run Ruff.
3. Run mypy.
4. Review the diff.
5. Report any unresolved risks.