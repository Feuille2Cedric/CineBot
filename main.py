import asyncio
from discord.ext import commands
from infrastructure.db.pool import create_pool
from infrastructure.db.schema import ensure_schema
from config.settings import DISCORD_TOKEN, INTENTS

class QuizBot(commands.Bot):
    async def setup_hook(self):
        # DB
        self.db = await create_pool()
        await ensure_schema(self.db)

        # Charge l’extension UNE SEULE FOIS (utilise setup() si présent)
        await self.load_extension("commands.quiz_cog")

    async def on_ready(self):
        print(f"[READY] Connecté en tant que {self.user}")

async def main():
    bot = QuizBot(command_prefix="!", intents=INTENTS)
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
