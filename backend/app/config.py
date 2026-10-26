"""Runtime configuration.

Values are read by pydantic-settings from (in order of precedence) real environment variables, then a
``.env`` file at the repository root. Field names map case-insensitively to env vars, e.g.
``nebius_api_key`` <- ``NEBIUS_API_KEY``. See ``.env.example`` for the full list.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Nebius Token Factory. No fake default: code paths that need a key must check
    # ``has_nebius_key`` and fall back to offline replay instead of sending a bogus key.
    nebius_api_key: SecretStr | None = None
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1/"

    # Pinned model IDs — verify against the authenticated catalog snapshot (ticket C-T02).
    model_ultra: str = "nvidia/Nemotron-3-Ultra-550b-a55b"
    model_super: str = "nvidia/nemotron-3-super-120b-a12b"
    model_nano: str = "nvidia/nemotron-3-nano"
    model_vision: str = "nvidia/cosmos-reason-2"

    # Tavily (Best Use of Tavily bonus track)
    tavily_api_key: SecretStr | None = None

    # Runtime
    environment: str = "development"
    log_level: str = "INFO"
    sandbox_network_disabled: bool = True
    mock_external_calls: bool = False

    # Where the append-only ledger and run artifacts are written. Defaults to <repo>/runs, but must be
    # overridden when the package is installed elsewhere (e.g. inside the jobs/ Docker image).
    runs_dir: Path = REPO_ROOT / "runs"

    @property
    def has_nebius_key(self) -> bool:
        return bool(self.nebius_api_key and self.nebius_api_key.get_secret_value())

    @property
    def has_tavily_key(self) -> bool:
        return bool(self.tavily_api_key and self.tavily_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
