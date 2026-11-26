"""Service configuration.

`Settings` is read once by the service's composition root. The bootstrap and
the migrations read only `StorageSettings`, where the data lives. `CAPPER_*`
environment variables (from `.env` through Compose) override the defaults;
`OPENAI_API_KEY` is read without the prefix.
Provider clients are constructed in `agent/agent.py`.
"""

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from capper.time import valid_zone


class StorageSettings(BaseSettings):
    """Where the data lives: the `capper-data` volume at `/app/data`."""

    # Compose passes `.env` to the container as environment variables; no file is read here.
    model_config = SettingsConfigDict(env_prefix="CAPPER_", extra="ignore")

    database_url: str = "sqlite+aiosqlite:////app/data/capper.db"
    jwt_public_key_path: str = "/app/data/keys/dev_public.pem"
    jwt_private_key_path: str = "/app/data/keys/dev_private.pem"


class Settings(StorageSettings):
    """Everything the service reads."""

    # Models
    chat_model: str = "openai:gpt-6.1-terra"
    compaction_model: str = "openai:gpt-6-luna"
    openai_api_key: SecretStr = Field(
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key")
    )

    # Provider calls
    model_connect_timeout_seconds: float = 5.0
    turn_timeout_seconds: float = 60.0

    # Context budget, clearing and compaction
    history_budget_tokens: int = 20_000
    compaction_trigger_ratio: float = 0.75
    compaction_target_ratio: float = 0.40
    tool_results_kept: int = 5
    min_clear_tokens: int = 2_000

    # Per-turn limits
    max_tool_calls_per_turn: int = 10
    tool_result_max_chars: int = 8_000
    max_message_chars: int = 8_000
    max_output_tokens: int = 4_096
    output_retries: int = 1

    # Saved user data
    guidance_max_notes: int = 30
    guidance_max_chars: int = 300
    avoid_list_max: int = 100

    # Time: for users without a time zone of their own
    default_timezone: str = "UTC"

    # Identity
    cache_key_secret: SecretStr
    jwt_issuer: str = "carton-caps-auth"
    jwt_audience: str = "capper"
    demo_session_minutes: int = 60

    # Provenance: the git commit the image was built from, when known.
    git_sha: str | None = None

    # Observability. `None` exports no traces (for a process without a collector).
    otlp_endpoint: str | None = "http://traces:4318"
    model_prices: dict[str, tuple[float, float, float]] = Field(
        default_factory=lambda: {
            # Per million tokens: input, cached input, output. Configurable estimates for the
            # trace's cost attribute, not billing.
            "openai:gpt-6.1-terra": (1.0, 0.05, 5.0),
            "openai:gpt-6-luna": (0.10, 0.01, 0.50),
        }
    )

    @model_validator(mode="after")
    def _check(self) -> Settings:
        if not 0 < self.compaction_target_ratio < self.compaction_trigger_ratio <= 1:
            raise ValueError("expected 0 < compaction_target_ratio < compaction_trigger_ratio <= 1")
        if not valid_zone(self.default_timezone):
            raise ValueError(f"default_timezone {self.default_timezone!r} isn't an IANA zone")
        return self

    @property
    def compaction_trigger_tokens(self) -> int:
        return int(self.history_budget_tokens * self.compaction_trigger_ratio)

    @property
    def compaction_keep_tokens(self) -> int:
        return int(self.history_budget_tokens * self.compaction_target_ratio)
