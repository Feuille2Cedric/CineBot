
from dataclasses import dataclass
import os
import datetime

@dataclass
class Config:
    DATABASE_URL: str
    DISCORD_TOKEN: str
    PROPOSAL_CHANNEL_ID: int
    VALIDATED_CHANNEL_ID: int
    COMMANDS_CHANNEL_ID: int
    UPDATE_CHANNEL_ID: int
    QUIZ_ROLE_ID: int
    HOUR_QUESTIONS_DAILY: int
    MINUTE_QUESTIONS_DAILY: int
    CHECKS_REQUIRED: int
    QUIZ_START_DATE: datetime.date = datetime.date(2025, 7, 9)
    QUESTIONS_PAR_JOUR: int = 5

def _int_env(name: str, default: int | None = None) -> int:
    val = os.getenv(name)
    if val is None:
        if default is None:
            raise RuntimeError(f"Missing required env var: {name}")
        return default
    return int(val)

def _clean_int_env(name: str) -> int:
    raw = os.getenv(name, "")
    clean = raw.strip().lstrip("=")
    return int(clean)

def load_config() -> Config:
    return Config(
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
        DISCORD_TOKEN=os.getenv("DISCORD_TOKEN", ""),
        PROPOSAL_CHANNEL_ID=_int_env("PROPOSAL_CHANNEL_ID"),
        VALIDATED_CHANNEL_ID=_int_env("VALIDATED_CHANNEL_ID"),
        COMMANDS_CHANNEL_ID=_int_env("COMMANDS_CHANNEL_ID"),
        UPDATE_CHANNEL_ID=_int_env("UPDATE_CHANNEL_ID"),
        QUIZ_ROLE_ID=_clean_int_env("QUIZ_ROLE_ID"),
        HOUR_QUESTIONS_DAILY=_int_env("HOUR_QUESTIONS_DAILY"),
        MINUTE_QUESTIONS_DAILY=_int_env("MINUTE_QUESTIONS_DAILY"),
        CHECKS_REQUIRED=_int_env("CHECKS_REQUIRED"),
    )
