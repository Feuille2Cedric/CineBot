import asyncio
import discord
from discord.ext import commands
from helper_functions.config import load_config
from helper_functions.db import init_db, close_db
from helper_functions.logging import setup_logger
from helper_functions.scheduler import QuizScheduler
from commands.quiz import QuizCog
from commands.profile import ProfileCog
from commands.rankings import RankingCog
from commands.proposals import ProposalCog

async def main():
    cfg = load_config()
    logger = setup_logger()
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    pool = await init_db(cfg.DATABASE_URL, logger=logger)

    bot.cfg = cfg
    bot.db = pool
    bot.logger = logger

    await bot.add_cog(QuizCog(bot))
    await bot.add_cog(ProfileCog(bot))
    await bot.add_cog(RankingCog(bot))
    await bot.add_cog(ProposalCog(bot))

    scheduler = QuizScheduler(bot)
    scheduler.start()

    try:
        await bot.start(cfg.DISCORD_TOKEN)
    finally:
        await close_db(pool)

if __name__ == "__main__":
    asyncio.run(main())
