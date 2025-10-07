import os
import asyncio
import datetime
import discord
from discord.ext import commands
import asyncpg

from function_helpers.constants import (
    DATABASE_URL, DISCORD_TOKEN, INTENTS,
)
from function_helpers import db as dbh
from commands.quiz_cog import QuizCog

# ── Création du bot ────────────────────────────────────────────────────────────
bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ── Events de base ────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[READY] Connecté en tant que {bot.user}")
    # Pool DB partagée sur bot
    bot.db = await asyncpg.create_pool(DATABASE_URL)

    # Création auto des tables si besoin
    await dbh.ensure_schema(bot.db)

    # Charger le COG principal (commandes + events + tâches)
    if not bot.get_cog("QuizCog"):
        await bot.add_cog(QuizCog(bot))
    print("[READY] Cogs chargés & schéma ok.")

# ── Lancement ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN manquant dans l'environnement.")
    bot.run(DISCORD_TOKEN)
