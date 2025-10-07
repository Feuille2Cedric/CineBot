from discord.ext import commands
from config.settings import COMMANDS_CHANNEL_ID
from app.domain.repositories import QuestionRepo

class QCmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.qrepo: QuestionRepo = bot.repos["questions"]

    @commands.command(name="q")
    async def q(self, ctx: commands.Context):
        if ctx.channel.id != COMMANDS_CHANNEL_ID:
            await ctx.send("Cette commande n'est autorisée que dans le salon de commandes.")
            return
        row = await self.qrepo.random_qa()
        if not row:
            await ctx.send("Aucune question disponible.")
            return
        msg = await ctx.send(f"**Question :** {row.question}\n||{row.answer}||")
        for e in ('✅', '❌', '🚮'):
            await msg.add_reaction(e)

async def setup(bot):
    if bot.get_cog("QCmd") is None:
        await bot.add_cog(QCmd(bot))
