from discord.ext import commands
from helper_functions.scores import get_user_totals
from helper_functions.embeds import profile_embed
from helper_functions.logging import log_command

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sp")
    @log_command
    async def profile(self, ctx):
        stats = await get_user_totals(self.bot.db, ctx.author.id)
        await ctx.send(embed=profile_embed(ctx.author, stats))
