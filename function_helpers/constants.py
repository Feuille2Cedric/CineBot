import os
import datetime
import discord

# Intents
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.reactions = True

# Env
DATABASE_URL          = os.getenv("DATABASE_URL")
DISCORD_TOKEN         = os.getenv("DISCORD_TOKEN")

PROPOSAL_CHANNEL_ID   = int(os.getenv("PROPOSAL_CHANNEL_ID", "0"))
VALIDATED_CHANNEL_ID  = int(os.getenv("VALIDATED_CHANNEL_ID", "0"))
COMMANDS_CHANNEL_ID   = int(os.getenv("COMMANDS_CHANNEL_ID", "0"))
UPDATE_CHANNEL_ID     = int(os.getenv("UPDATE_CHANNEL_ID", "0"))

# Rôle Quiz — nettoyage comme dans l’ancien code
_raw_quiz_role_id     = os.getenv("QUIZ_ROLE_ID", "")
print(f"[DEBUG] Valeur brute QUIZ_ROLE_ID depuis env : '{_raw_quiz_role_id}'")
_clean_quiz_role_id   = _raw_quiz_role_id.strip().lstrip("=")
print(f"[DEBUG] Valeur nettoyée QUIZ_ROLE_ID : '{_clean_quiz_role_id}'")
QUIZ_ROLE_ID          = int(_clean_quiz_role_id) if _clean_quiz_role_id else 0
print(f"[DEBUG] QUIZ_ROLE_ID en int = {QUIZ_ROLE_ID}")

HOUR_QUESTIONS_DAILY  = int(os.getenv("HOUR_QUESTIONS_DAILY", "9"))
MINUTE_QUESTIONS_DAILY= int(os.getenv("MINUTE_QUESTIONS_DAILY", "0"))
CHECKS_REQUIRED       = int(os.getenv("CHECKS_REQUIRED", "2"))

QUIZ_START_DATE       = datetime.date(2025, 7, 9)
QUESTIONS_PAR_JOUR    = 5
