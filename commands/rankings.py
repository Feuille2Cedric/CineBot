from discord.ext import commands
from helper_functions.scores import get_weekly_ranking
from helper_functions.embeds import ranking_embed
from helper_functions.logging import log_command

class RankingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sr")
    @log_command
    async def weekly(self, ctx):
        rows = await get_weekly_ranking(self.bot.db)
        lines = []
        for i, (uid, correct, attempts) in enumerate(rows, start=1):
            lines.append(f"{i}. <@{uid}> — {correct} / {attempts}")
        await ctx.send(embed=ranking_embed("Classement hebdo", lines))
