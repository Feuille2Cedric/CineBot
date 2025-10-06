import os
from dataclasses import dataclass

def _get_int_env(name: str, default: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        if default is None:
            raise ValueError(f"Missing required env var: {name}")
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"Env var {name} must be an integer, got: {raw!r}")

@dataclass(frozen=True)
class Config:
    DATABASE_URL: str
    DISCORD_TOKEN: str
    PROPOSAL_CHANNEL_ID: int
    VALIDATED_CHANNEL_ID: int
    COMMANDS_CHANNEL_ID: int
    HOUR_QUESTIONS_DAILY: int
    MINUTE_QUESTIONS_DAILY: int
    CHECKS_REQUIRED: int

def load_config() -> Config:
    db_url = os.getenv("DATABASE_URL")
    token = os.getenv("DISCORD_TOKEN")
    if not db_url:
        raise ValueError("Missing DATABASE_URL")
    if not token:
        raise ValueError("Missing DISCORD_TOKEN")

    return Config(
        DATABASE_URL=db_url,
        DISCORD_TOKEN=token,
        PROPOSAL_CHANNEL_ID=_get_int_env("PROPOSAL_CHANNEL_ID"),
        VALIDATED_CHANNEL_ID=_get_int_env("VALIDATED_CHANNEL_ID"),
        COMMANDS_CHANNEL_ID=_get_int_env("COMMANDS_CHANNEL_ID"),
        HOUR_QUESTIONS_DAILY=_get_int_env("HOUR_QUESTIONS_DAILY", 19),
        MINUTE_QUESTIONS_DAILY=_get_int_env("MINUTE_QUESTIONS_DAILY", 42),
        CHECKS_REQUIRED=_get_int_env("CHECKS_REQUIRED", 1),
    )
