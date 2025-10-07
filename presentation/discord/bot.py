from discord.ext import commands
from config.settings import INTENTS
from infrastructure.db.pool import create_pool
from infrastructure.db.schema import ensure_schema
from infrastructure.db.repositories_pg import (
    PgQuestionRepo, PgDayCounterRepo, PgDailyMessageRepo, PgScoreRepo
)

class QuizBot(commands.Bot):
    async def setup_hook(self):
        # DB
        self.pool = await create_pool()
        await ensure_schema(self.pool)

        # DI
        self.repos = {
            "questions": PgQuestionRepo(self.pool),
            "days": PgDayCounterRepo(self.pool),
            "daily_msg": PgDailyMessageRepo(self.pool),
            "scores": PgScoreRepo(self.pool),
        }

        # Extensions (chargées une seule fois)
        await self.load_extension("presentation.discord.cogs.events")
        await self.load_extension("presentation.discord.cogs.scheduler")
        await self.load_extension("presentation.discord.commands.propose")
        await self.load_extension("presentation.discord.commands.q")
        await self.load_extension("presentation.discord.commands.sp")
        await self.load_extension("presentation.discord.commands.sr")
        await self.load_extension("presentation.discord.commands.annonce_nouveautes")
        await self.load_extension("presentation.discord.commands.aide")

    async def on_ready(self):
        print(f"[READY] Connecté en tant que {self.user}")

async def create_bot() -> QuizBot:
    return QuizBot(command_prefix="!", intents=INTENTS)
