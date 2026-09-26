from functools import cache

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    chembl_client_base_url: HttpUrl = HttpUrl("https://www.ebi.ac.uk/chembl/api/data")


@cache
def get_settings() -> Settings:
    """Return the process-wide validated application configuration."""
    return Settings()
