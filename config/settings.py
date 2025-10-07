import os
import datetime
import discord

# ENV
DATABASE_URL           = os.getenv("DATABASE_URL")
DISCORD_TOKEN          = os.getenv("DISCORD_TOKEN")

PROPOSAL_CHANNEL_ID    = int(os.getenv("PROPOSAL_CHANNEL_ID", "0"))
VALIDATED_CHANNEL_ID   = int(os.getenv("VALIDATED_CHANNEL_ID", "0"))
COMMANDS_CHANNEL_ID    = int(os.getenv("COMMANDS_CHANNEL_ID", "0"))
UPDATE_CHANNEL_ID      = int(os.getenv("UPDATE_CHANNEL_ID", "0"))

_raw_quiz_role_id      = os.getenv("QUIZ_ROLE_ID", "").strip().lstrip("=")
QUIZ_ROLE_ID           = int(_raw_quiz_role_id) if _raw_quiz_role_id else 0

HOUR_QUESTIONS_DAILY   = int(os.getenv("HOUR_QUESTIONS_DAILY", "9"))
MINUTE_QUESTIONS_DAILY = int(os.getenv("MINUTE_QUESTIONS_DAILY", "0"))
CHECKS_REQUIRED        = int(os.getenv("CHECKS_REQUIRED", "2"))

QUIZ_START_DATE        = datetime.date(2025, 7, 9)
QUESTIONS_PAR_JOUR     = 5

# Discord intents
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.reactions = True
