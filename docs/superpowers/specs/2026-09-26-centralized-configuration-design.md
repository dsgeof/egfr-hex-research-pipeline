# Centralized Configuration Design

## Goal

Provide one typed application configuration module that reads configuration from process environment variables and a project-level `.env` file. The first configured value is the ChEMBL client base URL.

## Architecture

Add `src/egfr_discovery/config.py` as infrastructure-level configuration. Domain and application modules will not import it. Bootstrap code and concrete adapters may obtain settings and inject primitive configuration values into constructed dependencies.

The module will define:

- `Settings`, derived from `pydantic_settings.BaseSettings`.
- `chembl_client_base_url`, represented by Pydantic's `HttpUrl` and defaulting to `https://www.ebi.ac.uk/chembl/api/data`.
- `get_settings()`, a zero-argument cached factory returning a validated `Settings` instance.

The environment variable name will be `CHEMBL_CLIENT_BASE_URL`; no project-specific prefix will be used.

## Configuration Sources and Precedence

`SettingsConfigDict` will configure `.env` loading with UTF-8 encoding. Pydantic's normal source priority will apply:

1. Explicit constructor arguments.
2. Process environment variables.
3. Values from `.env`.
4. Field defaults.

Unrelated entries in the shared `.env` file will be ignored. This permits existing settings such as `OPENAI_API_KEY` without forcing this focused change to model or consume them.

## Validation and Errors

Pydantic will validate both default and supplied values. Invalid or non-HTTP ChEMBL URLs will raise `pydantic.ValidationError` when settings are constructed. Errors will not be replaced with fallback values or silently coerced into valid URLs.

The cached accessor avoids repeated file and environment parsing during application execution. Tests and callers that deliberately need a reload can clear the accessor's cache before constructing settings again.

## Dependencies

No new direct dependency is required. The project already depends directly on `pydantic-settings`, which declares and installs `python-dotenv` for dotenv parsing. Application code will not import `python-dotenv` directly.

## Tests

Unit tests will verify:

- The documented ChEMBL URL is used by default.
- A value from a specified dotenv file is loaded.
- A process environment variable overrides a dotenv value.
- An invalid URL raises a validation error.
- Repeated calls to `get_settings()` return the cached instance.

Tests will isolate environment and dotenv state and clear the settings cache so execution order cannot affect results.

## Scope

This change adds the configuration module and its tests only. It will not alter the in-progress ChEMBL adapter, centralize unrelated existing variables, or refactor bootstrap code.
